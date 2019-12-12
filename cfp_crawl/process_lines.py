import argparse
import lxml.html
import sqlite3
import traceback


class LineProcessor:

    def get_texts_with_srcline(self, srcline: int, tag: str, indentation, texts: 'List'):
        """ Corner case of processing text for complex block with <br> since sourceline required
        """
        line_tuples = []
        for text in texts:
            line_tuples.append((srcline, text.strip(), tag, indentation))
        return line_tuples

    def process_complex_block(self, indentation, node):
        """ Processes nodes with text and elements
            - If <br> present, for each <br> tag get preceding node elements and texts if applicable
            - Else just get element and text
        """
        line_tuples = []
        br_nodes = node.xpath("./br")
        if br_nodes:
            for br_node in br_nodes:
                pre_els = br_node.xpath("./preceding-sibling::*[1]")
                pre_texts = br_node.xpath("./preceding-sibling::text()[1]")
                for pre_el in pre_els:
                    line_tuples += self.get_line_tuples(indentation + 1, pre_el)
                line_tuples += self.get_texts_with_srcline(br_node.sourceline - 1, node.xpath("name()"), indentation, pre_texts)
        else:
            els = node.xpath('./*')
            for el in els:
                line_tuples += self.get_line_tuples(indentation, el)
            line_tuples += self.get_texts(indentation, node)

        return line_tuples


    def get_texts(self, indentation, node: 'Selector'):
        """ Gets text(s) directly from element
        - Filters empty text
        """
        line_tuples = []
        possible_texts = [s.strip() for s in node.xpath('text()')]
        if not all(s == "" for s in possible_texts):
            texts = list(filter(lambda x: x != "", possible_texts))
            node_tag = node.xpath("name()")
            for text in texts:
                line_tuples.append((node.sourceline, text, node_tag, indentation))
        return line_tuples


    def is_single_level(self, node: 'Selector'):
        """ Checks if element is single level
        """
        children = node.xpath("./*")
        return not bool(children)


    def is_complex_block(self, node: 'Selector'):
        """ Checks if block is complex
            - Combination of tags and text in block
        """
        inner_tag_types = [n.xpath('name()') for n in node.xpath('./*')]
        inner_tags_present = bool(inner_tag_types)
        inner_text = [n.strip() for n in node.xpath('text()')]
        inner_text = list(filter(lambda x: x != "", inner_text))
        inner_text_present = bool(inner_text)
        return inner_tags_present and inner_text_present


    def get_line_tuples(self, indentation: int, node: 'Selector'):
        """Given root node, recursively inspects children for those containing text
        and returns them with their corresponding indentation levels
            - Checks for p block
        """
        line_tuples = []
        if node.xpath('name()') in ['script', 'style']:
            pass
        elif self.is_complex_block(node):
            line_tuples += self.process_complex_block(indentation, node)
        elif self.is_single_level(node):
            line_tuples += self.get_texts(indentation, node)
        else: # Only nested elements present
            children = node.xpath('./*')
            for child in children:
                line_tuples += self.get_line_tuples(indentation + 1, child)
        return line_tuples


def add_page_lines(filepath, start_index, end_index):
    """
    Get all lines of each conference page
    """
    line_processor = LineProcessor()

    cnx = sqlite3.connect(filepath)
    cur = cnx.cursor()
    conf_ids = cur.execute(
        "SELECT id FROM WikicfpConferences WHERE accessible LIKE '%Accessible%' ORDER BY id").fetchall()[start_index:end_index]
    for conf_id in conf_ids:
        conf_id = conf_id[0]
        print("======================== Processing Conference: {} ============================".format(conf_id))
        page_ids = cur.execute(
            "SELECT id FROM ConferencePages WHERE conf_id={} AND processed IS NULL AND content_type='html'".format(conf_id)).fetchall()
        for page_id in page_ids:
            page_id = page_id[0]
            html_string: str = cur.execute(
                "SELECT html FROM ConferencePages WHERE id={}".format(page_id)).fetchone()
            try:
                html_string = html_string[0]
                parsed_html: 'Selector' = lxml.html.fromstring(html_string)
                line_tuples: List[Tuple] = line_processor.get_line_tuples(indentation=0, node=parsed_html.xpath("body")[0])
                for line_tuple in line_tuples:
                    cur.execute("INSERT INTO PageLines (page_id, line_num, line_text, tag, indentation) VALUES (?, ?, ?, ?, ?)",
                                (page_id, *line_tuple))
                cur.execute(
                    "UPDATE ConferencePages SET processed=? WHERE id=?", ('Yes', page_id))
                cnx.commit()
            except Exception as e:
                cur.execute(
                    "UPDATE ConferencePages SET processed=? WHERE id=?", ('Error', page_id))
                print("========= Page ID: {} ========".format(page_id))
                print(traceback.format_exc())
    cur.close()
    cnx.close()


parser = argparse.ArgumentParser(description='')
parser.add_argument('filepath', type=str, help="Specify file to process lines")
args = parser.parse_args()
START_INDEX, END_INDEX = 0, 1000
add_page_lines(args.filepath, START_INDEX, END_INDEX)
