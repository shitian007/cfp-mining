import argparse
import re
import numpy as np
import pickle
import sqlite3
import string
import unicodedata
from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

def clean_punctuation(ltext: str):
    ltext = ltext.strip(string.punctuation) # Strip leading and trailing punctuation
    ltext = unicodedata.normalize("NFKD", ltext) # Normalize string to unicoded to remove splitting errors
    ltext = re.sub('\t|\r|\n|\(|\)|\"|\'', ' ', ltext) # Replace tabs and newlines with spaces
    ltext = re.sub(' +', ' ', ltext) # Remove multiple spacing
    ltext = ltext.strip()
    return ltext

class Clustering:

    def __init__(self, cur, ngram_range, dist_threshold):
        self.ngram_range = ngram_range
        self.ent_to_idx = None
        self.idx_to_ent = None
        self.ent_scores = None # Numpy array (num_ent, num_feats) of TF-IDF entity scores
        self.cluster_to_idx = None # Cluster num to entity idx
        self.idx_to_cluster = None # Entity idx to cluster num
        # Hiearchical Agglomerative Clustering
        self.hac = AgglomerativeClustering(distance_threshold=dist_threshold, n_clusters=None)

    def get_entities(self, ent_table: str):
        """ Get entities from database table
        """
        entities = cur.execute("SELECT DISTINCT name FROM {} ORDER BY name".format(ent_table)).fetchall()
        entities = sorted(list(set([clean_punctuation(org[0]) for org in entities])))
        # Create mapping of organization to idx for retrieval
        self.idx_to_ent = entities
        self.ent_to_idx = dict({entities[i]: i for i in range(len(entities))})
        return self.idx_to_ent, self.ent_to_idx

    def vectorize(self, entities):
        """ TF-IDF vectorize entities based on ngram_range
        """
        vectorizer = TfidfVectorizer(ngram_range=self.ngram_range)
        ent_scores = vectorizer.fit_transform(entities)
        return ent_scores.toarray()

    def cluster_ents(self, ent_scores, num_to_cluster):
        """ Performs HAC clustering with specified threshold distance
        """
        self.hac.fit(ent_scores[0:num_to_cluster])
        idx_to_cluster = self.hac.labels_
        num_clusters = max(idx_to_cluster)
        cluster_to_idx = {i:[] for i in range(num_clusters+1)}
        for i in range(num_to_cluster):
            cluster_num = self.hac.labels_[i]
            cluster_to_idx[cluster_num].append(i)

        self.cluster_to_idx = cluster_to_idx
        self.idx_to_cluster = idx_to_cluster
        return cluster_to_idx, idx_to_cluster


parser = argparse.ArgumentParser(description='')
parser.add_argument('db_filepath', type=str,
                    help="Specify database file to predict lines")
parser.add_argument('cluster_filepath', type=str,
                    help="Specify cluster file save location")
args = parser.parse_args()
cnx = sqlite3.connect(args.db_filepath)
cur = cnx.cursor()

clustering = Clustering(cur, (1,2), 0.8)
idx_to_ent, ent_to_idx = clustering.get_entities('Organizations')
print("Vectorizing {} organizations".format(len(idx_to_ent)))
ent_scores = clustering.vectorize(idx_to_ent)

# HAC
num_orgs_to_cluster = len(ent_to_idx)
num_orgs_to_cluster = 100
print("Clustering {} organizations".format(num_orgs_to_cluster))
cluster_to_idx, idx_to_cluster = clustering.cluster_ents(ent_scores, num_orgs_to_cluster)
print("Number of organizations: Original: {} | Clusters: {}".format(num_orgs_to_cluster, len(cluster_to_idx)))

# Pickle Clustering object
with open(args.cluster_filepath, 'wb') as cluster_file:
    pickle.dump(clustering, cluster_file, pickle.HIGHEST_PROTOCOL)
    print("File saved")