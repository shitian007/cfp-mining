import flair
import spacy
import string
from collections import defaultdict
from flair.data import Sentence
from flair.models import SequenceTagger
from .utils import Line, TxFn


class BlockExtractor:

    def __init__(self, cur, extraction_type):
        self.cur = cur
        # extraction_type of either 'gold' or 'dl_predicted' or 'svm_predicted'
        self.extract_type = extraction_type

    def get_relevant_lines(self, conf_id: int):
        """ Get lines with label != undefined for Conference
        """
        page_ids = self.cur.execute(
            'SELECT id FROM ConferencePages WHERE conf_id={}'.format(conf_id)).fetchall()
        page_ids = [p[0] for p in page_ids]  # Page_id retrieval is tuple
        all_lines = []
        for page_id in page_ids:
            if self.extract_type == 'svm_prediction':
                lines = self.cur.execute("SELECT * FROM PageLines WHERE \
                                  page_id=? AND line_text!='' AND (svm_prediction!=?) \
                                  ORDER BY id", (page_id, 'Undefined')).fetchall()
            if self.extract_type == 'dl_prediction':
                lines = self.cur.execute("SELECT * FROM PageLines WHERE \
                                  page_id=? AND line_text!='' AND (dl_prediction!=?) \
                                  ORDER BY id", (page_id, 'Undefined')).fetchall()
            elif self.extract_type == 'gold':
                lines = self.cur.execute("SELECT * FROM PageLines WHERE \
                                  page_id=? AND line_text!='' AND label!=? \
                                  ORDER BY id", (page_id, 'Undefined')).fetchall()
            else:  # Undefined extraction type
                return []
            all_lines += [Line(l) for l in lines]
        return all_lines

    def get_relevant_blocks(self, conf_id: int, indent_diff_thresh: int, lnum_diff_thresh: int):
        """ Provides a mapping of Role Labels to Person/Affiliations
        - Groups only for 'Role Label' within threshold of indentation or line_num difference
        - Returns dictionary of {role_label Line : List of Person/Aff Lines} for further processing
        """

        def within_threshold(line, prev_line, rl_line):
            """ Ensure threshold diffs 
            - between indentation of line and role_label
            - between line_num of line and prev_labelled
            """
            indent_thresh = abs(int(line.indentation) -
                                int(rl_line.indentation)) < indent_diff_thresh
            lnum_thresh = abs(
                int(line.num) - int(prev_line.num)) < lnum_diff_thresh
            return indent_thresh and lnum_thresh

        relevant_lines = self.get_relevant_lines(conf_id)
        mapping = defaultdict(list)

        role_label: 'Line' = None
        prev_labelled: 'Line' = None  # Keeps track of last labelled line under current label

        for line in relevant_lines:
            label = line.label if self.extract_type == 'gold' else line.svm_prediction if self.extract_type == 'svm_prediction' else line.dl_prediction
            if label == "Role-Label":
                role_label = line
                prev_labelled = line
            elif role_label:
                if within_threshold(line, prev_labelled, role_label):
                    if mapping[role_label]:
                        mapping[role_label].append(line)
                    else:
                        mapping[role_label] = [line]
                    prev_labelled = line
            else:
                pass

        return mapping


class LineNERExtractor:
    def __init__(self):
        self.spacy_nlp = spacy.load("en_core_web_md")
        self.flair_tagger = SequenceTagger.load('ner')

    def get_line_parts_spacy(self, line: 'Line'):
        """ Retrieves PERSON/ORG/GPE
        - Change to PER/ORG/LOC for consistency with flair
        """
        spacy_flair_tag_map = {
            "PERSON": "PER",
            "GPE": "LOC"
        }
        line_parts = defaultdict(lambda: None)
        res = self.spacy_nlp(line.text)
        for ent in res.ents:
            ent_label = ent.label_
            if ent.label_ == "PERSON" or ent.label_ == "GPE":
                ent_label = spacy_flair_tag_map[ent.label_]
            # Currently not saving for multiple ner extractions
            if not line_parts[ent_label]:
                line_parts[ent_label] = ent.string
            print(f"{ent}, {ent.label_}| ", end="")
        print()
        return line_parts

    def get_line_parts_flair(self, line: 'Line'):
        """ Split by comma since Flair is insensitive to commas
        """
        line_parts = defaultdict(lambda: None)
        for part in line.text.split(","):
            part = Sentence(part)
            self.flair_tagger.predict(part)
            for entity in part.get_spans('ner'):
                # Currently not saving for multiple ner extractions
                if not line_parts[entity.tag]:
                    line_parts[entity.tag] = entity.text
                print(f"{entity.text}, {entity.tag}| ", end="")
        print()
        return line_parts


class LineInfoExtractor:
    """ Extract Person/Organization/Conference-Role relationships for individual conferences
    - TODO Retrieve complex containing Role Information
    - TODO Spelling Correction for countries to prevent classification as organization
    - TODO Handle multiple Person/Organization/Role extraction for individual lines
    - TODO Save unprocessed affiliations
    """

    def __init__(self, cur, extract_type, ner_extract_type):
        self.cur = cur
        # extraction_type of either 'gold' or 'dl_predicted' or 'svm_predicted'
        self.extract_type = extract_type
        self.ner_extract_type = ner_extract_type
        # Set during block processing
        self.conference = None
        # NER
        self.line_ner_extractor = LineNERExtractor()

    def get_line_parts(self, line: 'Line'):
        if self.ner_extract_type == 'flair':
            return self.line_ner_extractor.get_line_parts_flair(line)
        elif self.ner_extract_type == 'spacy':
            return self.line_ner_extractor.get_line_parts_spacy(line)
        else:
            raise ValueError("Unknown NER extraction type")

    def process_complex(self, line: 'Line', role_label: 'Line'):
        """ Processes Complex Line
        - Adds Person to Conference
        """
        line_parts = self.get_line_parts(line)
        if line_parts['PER']:
            person_id = self.add_person(line_parts['PER'])
            self.add_role_rel(person_id, role_label.text)
        if line_parts['ORG']:
            org_id = self.add_organization(line_parts['ORG'])
            if line_parts['LOC']:
                self.update_org_loc(org_id, line_parts['LOC'])

        if line_parts['PER'] and line_parts['ORG']:  # Add affiliation relation
            self.add_affiliation_rel(person_id, org_id)

    def process_pair(self, person: 'Line', affiliation: 'Line', role_label: 'Line'):
        """ Creates affiliation relation between Person and Organization
        - Adds Person to Conference
        """
        print("{}, PER| ".format(person.text), end='')
        person_id = self.add_person(person.text)
        self.add_role_rel(person_id, role_label.text)
        line_parts = self.get_line_parts(affiliation)
        if line_parts['ORG']:
            org_id = self.add_organization(line_parts['ORG'])
            if line_parts['LOC']:
                self.update_org_loc(org_id, line_parts['LOC'])
            self.add_affiliation_rel(person_id, org_id)
        else:
            print("!!!!!!! Affiliation not processed: {}".format(affiliation.text))

    def process_block(self, role_label: 'Line', content_lines: 'List[Line]'):
        """ Processes singular block of PageLine ids corresponding to role label and following content
        """
        print("================= {} =============".format(role_label.text))
        cur_idx = 0
        u_person, u_aff = None, None
        for cur_line in content_lines:

            label = cur_line.label if self.extract_type == 'gold' else\
                cur_line.svm_prediction if self.extract_type == 'svm_prediction' else cur_line.dl_prediction

            if label == 'Complex':  # Assume contains person and affiliation
                self.process_complex(cur_line, role_label)
            else:
                if label == 'Person':
                    u_person = cur_line
                    if u_aff:  # Should pair person with affiliation
                        self.process_pair(u_person, u_aff, role_label)
                        u_person, u_aff = None, None
                elif label == 'Affiliation':
                    u_aff = cur_line
                    if u_person:  # Should pair person with affiliation
                        self.process_pair(u_person, u_aff, role_label)
                        u_person, u_aff = None, None
                else:
                    print("Unexpected Label: {} [{}]".format(
                        cur_line.label, cur_line.text))

            cur_idx += 1
            prev_line = cur_line

    def process_conference(self, conference: 'Conference'):
        """ Processes relevant retrieved from BlockExtractor
        """
        self.conference = conference
        self.sql_conf_id = conference.id
        # Process relevant blocks of conference
        for rl_id, content_ids in conference.blocks.items():
            self.process_block(rl_id, content_ids)

    def add_person(self, person: str):
        self.cur.execute(
            "INSERT INTO Persons (name) VALUES (?)", (person,))
        sql_oid = self.cur.lastrowid
        return sql_oid

    def add_organization(self, org: str):
        self.cur.execute(
            "INSERT INTO Organizations (name) VALUES (?)", (org,))
        sql_oid = self.cur.lastrowid
        return sql_oid

    def add_affiliation_rel(self, person_id: 'Tuple', org_id: 'Tuple'):
        self.cur.execute("INSERT OR IGNORE INTO PersonOrganization (org_id, person_id)\
                VALUES (?, ?)", (org_id, person_id))

    def add_role_rel(self, person_id: 'Tuple', role: str):
        self.cur.execute("INSERT OR IGNORE INTO PersonRole (role_type, conf_id, person_id)\
                VALUES (?, ?, ?)", (role, self.sql_conf_id, person_id))

    def update_org_loc(self, org_id: int, loc: str):
        self.cur.execute(
            "UPDATE Organizations SET location=? WHERE id=?", (loc, org_id))
