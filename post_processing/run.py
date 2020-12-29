import argparse
import sqlite3

from process_lines import add_page_lines
from svm_line_classification.svm_predict_lines import svm_predict_lines
from dl_line_classification.rnn_predict_lines import rnn_predict_lines, LineClassifier
from dl_line_classification.data_generation import DataGenerator
from dl_line_classification.train import train_dl_classification_model
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
GENERATE_VOCAB = False
TRAIN_LINE_CLASSIFIER = True
PREDICT_LINES_DL = False
EXTRACT_INFO = False
CONF_IDS = [i for i in range(1, 200)]

""" Process Lines
- Processes HTML of each page to lines, ordered by conference_id
"""
if PROCESS_LINES:
    add_page_lines(cnx, CONF_IDS)
    cnx.commit()

""" Generate Vocab
- Generate the necessary files for line classification
"""
if GENERATE_VOCAB:
    data_generator = DataGenerator(cur)
    data_generator.generate_vocab()
VOCAB_FILEPATH = "./dl_line_classification/vocab.txt"
LABEL_VOCAB_FILEPATH = "./dl_line_classification/label_vocab.txt"
TAG_VOCAB_FILEPATH = "./dl_line_classification/tag_vocab.txt"

""" Train line classifier
- Trains a line classifier based on labelled lines in current db
"""
if TRAIN_LINE_CLASSIFIER:
    train_dl_classification_model(cnx, VOCAB_FILEPATH, LABEL_VOCAB_FILEPATH, TAG_VOCAB_FILEPATH)

""" Predict Lines
- Adds prediction of line information, ordered by conference_id
"""
MODEL_FILEPATH = "./dl_line_classification/line_classifier"
if PREDICT_LINES_DL:
    rnn_predict_lines(cnx, MODEL_FILEPATH,
                      VOCAB_FILEPATH, LABEL_VOCAB_FILEPATH, TAG_VOCAB_FILEPATH,
                      CONF_IDS)
    cnx.commit()

""" Extraction of Conference - Person - Affiliation information
"""
EXTRACT_FROM = 'websites' # Type of content for extraction: websites / proceedings
EXTRACT_TYPE = 'dl_prediction' # Type of label: dl_prediction / gold
INDENT_DIFF_THRESHOLD = 12
LINENUM_DIFF_THRESHOLD = 10
if EXTRACT_INFO:
    extract_line_information(cnx, EXTRACT_FROM, EXTRACT_TYPE,
                             INDENT_DIFF_THRESHOLD, LINENUM_DIFF_THRESHOLD,
                             CONF_IDS)

cur.close()
cnx.close()
