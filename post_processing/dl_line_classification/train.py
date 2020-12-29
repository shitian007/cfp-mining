import sqlite3
import torch
import torch.nn as nn
import torch.optim as optim
from texar.torch.data.vocabulary import Vocab
from texar.torch.data import TrainTestDataIterator
from .rnn_predict_lines import RNNLinePredictor, LineClassifier, Dataset

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
EPOCHS = 10
BATCH_SIZE = 64
WEIGHTS = torch.tensor([5, 5, 5, 5, 0.5], dtype=torch.float32).to(device)

def train_dl_classification_model(cnx, vocab_filepath, label_vocab_filepath, tag_vocab_filepath):
    print("============================== Training line classification model =================================")
    rnn_line_predictor = RNNLinePredictor(None, vocab_filepath, label_vocab_filepath, tag_vocab_filepath)

    print("Generating dataset from db")
    cur = cnx.cursor()
    lines = cur.execute("SELECT id, label, tag, indentation, line_text FROM PageLines WHERE label IS NOT NULL LIMIT 100000").fetchall()
    rnn_line_predictor.create_labelled_lines_file(
        lines,
        "./dl_line_classification/train.txt",
        "./dl_line_classification/val.txt",
      )

    print("Loading vocabs")
    vocab = Vocab(vocab_filepath)
    tag_vocab = Vocab(tag_vocab_filepath)
    label_vocab = Vocab(label_vocab_filepath)

    print("Loading dataset")
    train_data = Dataset('./dl_line_classification/train.txt', vocab, label_vocab, tag_vocab, hparams={'batch_size': BATCH_SIZE})
    val_data = Dataset('./dl_line_classification/val.txt', vocab, label_vocab, tag_vocab, hparams={'batch_size': BATCH_SIZE})
    data_iterator = TrainTestDataIterator(train=train_data, val=val_data)

    print("Creating classifier")
    line_classifier = LineClassifier(vocab, device)
    line_classifier.to(device)

    loss_criterion = nn.CrossEntropyLoss(weight=WEIGHTS)
    optimizer = optim.SGD(line_classifier.parameters(), lr=0.001, momentum=0.9)

    print(device)
    for epoch in range(EPOCHS):
        num_batch = 0
        print("Epoch: {0}".format(epoch + 1))
        for batch in data_iterator.get_train_iterator():
            label_ids = batch["label_ids"].flatten().to(device)
            outputs = line_classifier(batch)
            loss = loss_criterion(outputs, label_ids)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            if num_batch % 50 == 0:
                print(loss)
            num_batch += 1

        num_batch = 0
        total_val_loss = 0
        total_correct_labels = 0
        total_instances = 0
        for batch in data_iterator.get_val_iterator():
            label_ids = batch["label_ids"].flatten().to(device)
            outputs = line_classifier(batch)
            loss = loss_criterion(outputs, label_ids)

            output_label_ids = torch.argmax(outputs, dim=1)
            total_correct_labels += (output_label_ids == label_ids).sum()
            total_val_loss += loss.item()
            total_instances += len(label_ids)
            num_batch += 1

        print("Percentage correct labels: {:f}".format(total_correct_labels / total_instances))
        print("Loss: {:f}".format(total_val_loss / num_batch))

    torch.save(line_classifier, "./dl_line_classification/line_classifier")


if __name__ == "__main__":
    vocab_fp = "./dl_line_classification/vocab.txt"
    label_vocab_fp = "./dl_line_classification/label_vocab.txt"
    tag_vocab_fp = "./dl_line_classification/tag_vocab.txt"

    cnx = sqlite3.connect("../crawls/all_dec_19/all_dec_19.db")

    train_dl_classification_model(cnx, vocab_fp, label_vocab_fp, tag_vocab_fp)



