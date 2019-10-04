import re
import sqlite3
from enum import Enum
from typing import List
from flair.data import Sentence
from flair.models import SequenceTagger
from segtok.segmenter import split_single

class ConferenceHelper:
    """
    Database helper for Conference Items
    """

    @staticmethod
    def create_db(dbpath):
        """
        Create the necessary tables for the conference database
        """
        conn = sqlite3.connect(str(dbpath))
        cur = conn.cursor()
        conferences = "CREATE TABLE IF NOT EXISTS Conferences (\
            id INTEGER NOT NULL PRIMARY KEY,\
            title TEXT NOT NULL UNIQUE,\
            url TEXT,\
            timetable TEXT,\
            year INTEGER,\
            wayback_url TEXT,\
            categories TEXT,\
            aux_links TEXT,\
            persons TEXT,\
            accessible TEXT\
        );"

        urls = "CREATE TABLE IF NOT EXISTS Urls (\
            id INTEGER NOT NULL PRIMARY KEY,\
            conf_id INTEGER NOT NULL REFERENCES Conference(id),\
            url TEXT\
        );"

        cur.execute(conferences)
        cur.execute(urls)
        conn.commit()
        cur.close()
        conn.close()


    @staticmethod
    def add_conf_db(conference: 'Conference', dbpath: str):
        """
        Adds Conference object and writes to specified database
        """
        conn = sqlite3.connect(str(dbpath))
        cur = conn.cursor()

        # TODO String formatting not foolproof, i.e. Xi'an
        cur.execute(
            "INSERT OR REPLACE INTO Conferences\
            (title, url, timetable, year, wayback_url, categories, accessible) \
            VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                str(conference['title']),
                str(conference['url']),
                str(conference['timetable']),
                str(conference['year']),
                str(conference['wayback_url']),
                str(conference['categories']),
                str(conference['accessible'])
            )
        )
        conf_row_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()
        return conf_row_id


    @staticmethod
    def add_url_db(url: str, conf_row_id: int, dbpath: str):
        conn = sqlite3.connect(str(dbpath))
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO Urls\
            (conf_id, url) \
            VALUES (?, ?)",
            (conf_row_id, url)
        )
        conn.commit()
        cur.close()
        conn.close()


    @staticmethod
    def mark_accessibility(url: str, access_status: str, dbpath: str):
        """
        Marks the accessibility attribute of a conference
        """
        conn = sqlite3.connect(str(dbpath))
        cur = conn.cursor()
        cur.execute(
            'UPDATE Conferences SET accessible = "{}" WHERE url = "{}"'.format(access_status, url)
            )
        conn.commit()
        cur.close()
        conn.close()


class NER:

    ner_engine = SequenceTagger.load('ner')

    @staticmethod
    def get_persons_textblocks(text_blocks: List[List]):
        """
        Processes textblocks from within wikicfp conference page
        """
        persons = []
        for text_block in text_blocks:
            for line in text_block:
                retrieved_persons: List[str] = NER.get_persons_line(line)
                persons += retrieved_persons
        return persons


    @staticmethod
    def get_persons_line(line: str):
        """
        Gets detected persons from line possibly containing multiple sentences
        """
        persons = []
        sentences: List[str] = list(filter(lambda sent: sent, split_single(line)))
        sentences: List[Sentence] = [Sentence(sent) for sent in sentences]
        for sentence in sentences:
            NER.ner_engine.predict(sentence)
            for entity in sentence.get_spans('ner'):
                if 'PER' in entity.tag:
                    persons.append(entity.text)
        return persons






