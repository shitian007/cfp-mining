import argparse
import sqlite3

from neo4j import GraphDatabase
from process_lines import add_page_lines
from svm_line_classification.svm_predict_lines import predict_conference_lines
from info_extraction import extract_line_information

parser = argparse.ArgumentParser(description='')
parser.add_argument('db_filepath', type=str,
                    help="Specify database file to predict lines")
args = parser.parse_args()

cnx = sqlite3.connect(args.db_filepath)
cur = cnx.cursor()

# Indexes of accessible conferences to process
PROCESS_LINES = False
PREDICT_LINES_SVM = True
PREDICT_LINES_DL = False
EXTRACT = False
START_INDEX, END_INDEX = 0, 1

""" Process Lines
- Processes HTML of each page to lines, ordered by conference_id
"""
if PROCESS_LINES:
    add_page_lines(cur, START_INDEX, END_INDEX)
    cnx.commit()

""" Predict Lines
- Adds prediction of line information, ordered by conference_id
- Option between SVM and Deep-Learning approach
"""
SVM_FILEPATH = "./svm_line_classification/svm_01_12.pkl"
TFIDF_FILEPATH = "./svm_line_classification/tfidfvec_01_12.pkl"
CONFIDENCE_THRESHOLD = 0.8
if PREDICT_LINES_SVM:
    predict_conference_lines(cnx, SVM_FILEPATH, TFIDF_FILEPATH, # cnx needed for reading of sql for dataframe
                            START_INDEX, END_INDEX, CONFIDENCE_THRESHOLD)
    cnx.commit()
if PREDICT_LINES_DL:
    pass

# Start neo4j server and initialize constraints
uri = "bolt://localhost:7687"
driver = GraphDatabase.driver(uri, auth=("neo4j", "password"))
""" Extraction of Conference - Person - Affiliation information
"""
EXTRACT_TYPE = 'gold'
INDENT_DIFF_THRESHOLD = 3
LINENUM_DIFF_THRESHOLD = 10
if EXTRACT:
    extract_line_information(cur, driver, EXTRACT_TYPE, INDENT_DIFF_THRESHOLD, LINENUM_DIFF_THRESHOLD)

cur.close()
cnx.close()