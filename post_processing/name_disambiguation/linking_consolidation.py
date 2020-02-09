import argparse
import pickle
import sqlite3
from tfidf_clustering import Clustering
from nd_utils import clean_punctuation, create_tables


class Consolidator:

    def __init__(self, original_db_cnx, consolidated_db_cnx, clustering):
        self.original_db_cnx = original_db_cnx
        self.consolidated_db_cnx = consolidated_db_cnx
        self.clustering = clustering

    def org_cluster_rep(self, ent: str):
        """ Retrieves the cluster representative of the given organization
        """
        ent = clean_punctuation(ent)
        org_idx = self.clustering.ent_to_idx[ent]
        org_cluster = self.clustering.idx_to_cluster[org_idx]
        cluster_rep_idx = self.clustering.cluster_to_idx[org_cluster][0]
        cluster_rep = self.clustering.idx_to_ent[cluster_rep_idx]
        return cluster_rep

    def remove_duplicates(self, person_info: 'List'):
        """ Processes org to corresponding cluster_rep and keep only distinct Person-Org-Role tuples
        """
        person_info = [(person, self.org_cluster_rep(org), role)
                       for person, org, role in person_info]
        deduplicated = []
        for p_tuple in person_info:
            if p_tuple not in deduplicated:
                deduplicated.append(p_tuple)
        return deduplicated

    def process(self):
        """Consolidate Person/Org data post disambiguation

        Args:
            original_db_cnx ([type]): [description]
            consolidated_db_cnx ([type]): [description]
        """
        original_db_cur = self.original_db_cnx.cursor()
        consolidated_db_cur = self.consolidated_db_cnx.cursor()

        conferences = original_db_cur.execute(
            "SELECT id FROM WikicfpConferences ORDER BY id").fetchall()

        for conf_id in conferences:
            conf_id = conf_id[0]
            # Copy over table of conferences and conference pages
            conf = original_db_cur.execute(
                "SELECT * FROM WikicfpConferences WHERE id=?", (conf_id,)).fetchone()
            consolidated_db_cur.execute("INSERT INTO WikicfpConferences\
                        (id, series, title, url, timetable, year, wayback_url, categories, accessible, crawled)\
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", conf)
            conf_pages = original_db_cur.execute("SELECT id, conf_id, url, content_type, processed\
                                        FROM ConferencePages WHERE conf_id=?", (conf_id,)).fetchall()
            for conf_page in conf_pages:
                consolidated_db_cur.execute("INSERT INTO ConferencePages\
                            (id, conf_id, url, content_type, processed)\
                            VALUES (?, ?, ?, ?, ?)", conf_page)

            # Process Persons and Organizations
            persons_info = DatabaseHelper.get_persons_info(
                original_db_cur, conf_id)
            for person, org, role in self.remove_duplicates(persons_info):
                org_id = consolidated_db_cur.execute(
                    "SELECT id FROM Organizations WHERE name=?", (org,)).fetchone()
                if not org_id:
                    consolidated_db_cur.execute(
                        "INSERT INTO Organizations (name) VALUES (?)", (org,))
                    org_id = consolidated_db_cur.lastrowid
                else:
                    org_id = org_id[0]  # Fetch tuple

                person_id = consolidated_db_cur.execute(
                    "SELECT id FROM Persons WHERE name=? AND org_id=?", (person, org_id)).fetchone()
                if not person_id:
                    consolidated_db_cur.execute(
                        "INSERT INTO Persons (name, org_id) VALUES (?, ?)", (person, org_id))
                    person_id = consolidated_db_cur.lastrowid
                else:
                    person_id = person_id[0]
                consolidated_db_cur.execute("INSERT INTO PersonRole (role_type, conf_id, person_id) VALUES (?, ?, ?)",
                                           (role, conf_id, person_id))

        self.consolidated_db_cnx.commit()


parser = argparse.ArgumentParser(description='')
parser.add_argument('clustering_filepath', type=str,
                    help="Pickled Clustering")
parser.add_argument('original_db_filepath', type=str,
                    help="Database file to disambiguate (No alteration to this db)")
parser.add_argument('consolidated_db_filepath', type=str,
                    help="New consolidated database file save location")
args = parser.parse_args()

# Database connections and Clustering object
original_db_cnx = sqlite3.connect(args.original_db_filepath)
consolidated_db_cnx = sqlite3.connect(args.consolidated_db_filepath)
with open(args.clustering_filepath, 'rb') as cluster_file:
    clustering = pickle.load(cluster_file)

# Create necessary tables for consolidated data
create_tables(consolidated_db_cnx)
# Actual consolidation after disambiguation
consolidator = Consolidator(original_db_cnx, consolidated_db_cnx, clustering)
consolidator.process()

# Close connections
original_db_cnx.close()
consolidated_db_cnx.close()
