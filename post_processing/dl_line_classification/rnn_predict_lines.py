import re
import string
import sqlite3
import pandas as pd
import torch
import torch.nn as nn
import texar.torch as tx
from texar.torch.data import Vocab, DataIterator, Embedding
from texar.torch.modules import WordEmbedder, BidirectionalRNNEncoder, FeedForwardNetwork


class MyDataset(tx.data.DatasetBase):
    def __init__(self, data_path, vocab, label_vocab, tag_vocab, hparams=None, device=None):
        source = tx.data.TextLineDataSource(data_path)
        self.vocab = vocab
        self.label_vocab = label_vocab
        self.tag_vocab = tag_vocab
        super().__init__(source, hparams, device)

    def process(self, raw_example):
        """ Process tokenized lines from file
        """
        label = [raw_example[0]]
        tag = [raw_example[1]]
        indentation = [int(raw_example[2])]
        text = [t.lower() for t in raw_example[3:]]
        return {
            "label": label,
            "tag": tag,
            "indentation": indentation,
            "text": text,
            "label_id": self.label_vocab.map_tokens_to_ids_py(label),
            "tag_id": self.tag_vocab.map_tokens_to_ids_py(tag),
            "text_ids": self.vocab.map_tokens_to_ids_py(text)
        }

    def collate(self, examples):
        """ Batches processed examples
        """
        text = [ex["text"] for ex in examples]
        label = [ex["label"] for ex in examples]

        text_ids, lengths = tx.data.padded_batch(
            [ex["text_ids"] for ex in examples])
        # -3 for ridding of <BOS> <EOS> <PAD> idxs
        label_ids = [(ex["label_id"] - 3) for ex in examples]
        tag_ids = [(ex["tag_id"] - 3) for ex in examples]
        indentations = [ex["indentation"] for ex in examples]

        return tx.data.Batch(
            len(examples),
            text=text,
            label=label,
            text_ids=torch.from_numpy(text_ids),
            lengths=torch.tensor(lengths),
            label_ids=torch.tensor(label_ids),
            tag_ids=torch.tensor(tag_ids),
            indentations=torch.tensor(indentations)
        )


class LineClassifier(nn.Module):

    def __init__(self, vocab: 'Vocabulary'):
        super().__init__()
        glove_embedding = Embedding(
            vocab.token_to_id_map_py,
            hparams={
                "file": "./dl_line_classification/glove.6B.50d.txt",
                "read_fn": "load_glove",
                "dim": 50
            }
        )
        self.embedder = WordEmbedder(init_value=glove_embedding.word_vecs)
        self.encoder = BidirectionalRNNEncoder(input_size=50)
        self.linear_classifier = FeedForwardNetwork(hparams={
            "layers": [
                {"type": "Linear", "kwargs": {
                    "in_features": 514, "out_features": 5}
                 }
            ]
        })

    def get_parameters(self):
        return list(self.encoder.parameters()) + list(self.linear_classifier.parameters())

    def forward(self, batch):
        outputs, final_state = self.encoder(
            inputs=self.embedder(batch['text_ids']),
            sequence_length=batch['lengths'])
        ht, ct = final_state

        # Generate input to linear classification layer
        concated = torch.cat([ht[0], ht[-1]], dim=1)
        # Add in additional features
        concated = torch.cat(
            [concated, batch['tag_ids'].type(torch.float)], dim=1)
#         concated = torch.cat([concated, batch['indentations'].type(torch.float)], dim=1)
        lengths = batch['lengths'].unsqueeze(dim=1)
        concated = torch.cat([concated, lengths.type(torch.float)], dim=1)

        logits = self.linear_classifier(concated)
        return logits


class RNNLinePredictor:
    """ Loads Bidirectional LSTM Line Predictor for labelling of PageLines
    """

    def __init__(self, model_filepath, vocab_filepath, label_vocab_filepath, tag_vocab_filepath):
        data_hparams = {
            'batch_size': 32
        }
        self.vocab = Vocab(vocab_filepath)
        self.tag_vocab = Vocab(tag_vocab_filepath)
        self.label_vocab = Vocab(label_vocab_filepath)
        # TODO Delete 'file' arg: not actually used but required for instantiation
        self.data = MyDataset('./dl_line_classification/val.tsv',
                              self.vocab, self.label_vocab, self.tag_vocab,
                              hparams=data_hparams)
        self.line_classifier = torch.load(model_filepath)

    def get_label(self, logits: 'Tensor'):
        """ Retrieve label from logit output of model
        """
        # +3 taking into consideration <BOS> <EOS> <PAD> idxs (See dataset collate method)
        predicted_idx = logits.argmax(1).item() + 3
        predicted_label = self.label_vocab.id_to_token_map_py[predicted_idx]
        return 'Undefined' if predicted_label == '<UNK>' else predicted_label

    def predict_line(self, label, tag, indentation, line_text):
        """ Tokenizes line_text and returns prediction
        """
        tokens = line_text.split(" ")
        processed = self.data.process([label, tag, indentation] + tokens)
        batch = self.data.collate([processed])
        logits = self.line_classifier(batch)
        return self.get_label(logits)

    def clean(self, ltext: str):
        # Strip leading and trailing punctuation
        ltext = ltext.strip(string.punctuation)
        # Replace tabs and newlines with spaces
        ltext = re.sub('\t|\r|\n|\(|\)', ' ', ltext)
        ltext = re.sub(' +', ' ', ltext)  # Remove multiple spacing
        ltext = ltext.strip()
        return ltext

    def predict_lines(self, cur, pagelines_df: 'DataFrame'):
        line_generator = pagelines_df[[
            'id', 'label', 'tag', 'indentation', 'line_text']].iterrows()
        for line in line_generator:
            # Tuple retrieved
            pl_id, label, tag, indentation, line_text = line[1]
            line_text = self.clean(line_text)  # Formatting
            predicted_label = self.predict_line(
                label, tag, indentation, line_text)
            cur.execute(
                "UPDATE PageLines SET dl_prediction=? WHERE id=?", (predicted_label, pl_id))


def rnn_predict_lines(cnx, model_filepath,
                      vocab_filepath, label_vocab_filepath, tag_vocab_filepath,
                      start_index=0, end_index=-1):
    """ Predict pagelines for Conference and saves to database
    """
    cur = cnx.cursor()
    conf_ids = cur.execute(
        "SELECT id FROM WikicfpConferences WHERE accessible LIKE '%Accessible%' ORDER BY id").fetchall()[start_index:end_index]
    for conf_id in conf_ids:
        conf_id = conf_id[0]
        print("=========================== RNN Predicting for Conference {} =================================".format(conf_id))
        line_predictor = RNNLinePredictor(
            model_filepath, vocab_filepath, label_vocab_filepath, tag_vocab_filepath)
        confpages = cur.execute(
            "SELECT id, url FROM ConferencePages WHERE conf_id={}".format(conf_id)).fetchall()
        for confpage in confpages:
            confpage_id = confpage[0]
            pagelines_df = pd.read_sql(
                "SELECT * FROM PageLines WHERE page_id={}".format(confpage_id,), cnx)
            pagelines_df['line_text'] = pagelines_df['line_text'].str.strip()
            pagelines_df = pagelines_df[pagelines_df['line_text'] != ""]
            if len(pagelines_df) > 0:
                line_predictor.predict_lines(cur, pagelines_df)
            else:
                print("Empty DataFrame")
            cnx.commit()
    cur.close()
