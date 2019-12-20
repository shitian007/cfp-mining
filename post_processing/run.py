import argparse
import sqlite3

from neo4j import GraphDatabase
from process_lines import add_page_lines
from svm_line_classification.svm_predict_lines import svm_predict_lines
from dl_line_classification.rnn_predict_lines import rnn_predict_lines, LineClassifier
from info_extraction.extraction import extract_line_information
from utils import create_tables

parser = argparse.ArgumentParser(description='')
parser.add_argument('db_filepath', type=str,
                    help="Specify database file to predict lines")
args = parser.parse_args()

cnx = sqlite3.connect(args.db_filepath)
cur = cnx.cursor()
create_tables(cnx)

# Indexes of accessible conferences to process
PROCESS_LINES = False
PREDICT_LINES_SVM = False
PREDICT_LINES_DL = False
EXTRACT_INFO = True
START_INDEX, END_INDEX = 0, 1

""" Process Lines
- Processes HTML of each page to lines, ordered by conference_id
"""
if PROCESS_LINES:
    add_page_lines(cnx, START_INDEX, END_INDEX)
    cnx.commit()

""" Predict Lines
- Adds prediction of line information, ordered by conference_id
- Option between SVM and Deep-Learning approach
"""
SVM_FILEPATH = "./svm_line_classification/svm_01_12.pkl"
TFIDF_FILEPATH = "./svm_line_classification/tfidfvec_01_12.pkl"
CONFIDENCE_THRESHOLD = 0.8
if PREDICT_LINES_SVM:
    svm_predict_lines(cnx, SVM_FILEPATH, TFIDF_FILEPATH,  # cnx needed for reading of sql for dataframe
                      START_INDEX, END_INDEX, CONFIDENCE_THRESHOLD)
    cnx.commit()

VOCAB_FILEPATH = "./dl_line_classification/vocab.txt"
LABEL_VOCAB_FILEPATH = "./dl_line_classification/label_vocab.txt"
TAG_VOCAB_FILEPATH = "./dl_line_classification/tag_vocab.txt"
MODEL_FILEPATH = "./dl_line_classification/rnn_classifier"
if PREDICT_LINES_DL:
    rnn_predict_lines(cnx, MODEL_FILEPATH,
                      VOCAB_FILEPATH, LABEL_VOCAB_FILEPATH, TAG_VOCAB_FILEPATH,
                      START_INDEX, END_INDEX)
    cnx.commit()

# Start neo4j server and initialize constraints
uri = "bolt://localhost:7687"
driver = GraphDatabase.driver(uri, auth=("neo4j", "password"))
""" Extraction of Conference - Person - Affiliation information
"""
EXTRACT_TYPE = 'dl_prediction'
INDENT_DIFF_THRESHOLD = 3
LINENUM_DIFF_THRESHOLD = 10
if EXTRACT_INFO:
    extract_line_information(cnx, driver, EXTRACT_TYPE,
                             INDENT_DIFF_THRESHOLD, LINENUM_DIFF_THRESHOLD,
                             START_INDEX, END_INDEX)

cur.close()
cnx.close()
