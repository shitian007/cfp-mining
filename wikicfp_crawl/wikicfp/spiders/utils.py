import sqlite3
import scrapy
from enum import Enum
from typing import List
from flair.data import Sentence
from flair.models import SequenceTagger
from segtok.segmenter import split_single

class Constants(Enum):
    NO_YEAR = -1

class Conference(scrapy.Item):

    title = scrapy.Field()
    link = scrapy.Field()
    timetable = scrapy.Field()
    year = scrapy.Field()
    wayback_url = scrapy.Field()
    categories = scrapy.Field()
    aux_links = scrapy.Field()
    persons = scrapy.Field()

    @staticmethod
    def conference_to_csv(conference: 'Conference', filepath: str):
        """
        Takes a Conference object and writes to the specified filepath
        """
        with open(filepath, 'a+') as conference_csv:
            for value in conference.values():
                conference_csv.write('{}\t'.format(value))
            conference_csv.write('\n')


    @staticmethod
    def add_to_db(conference: 'Conference', dbpath: str):
        """
        Adds Conference object and writes to specified database
        """
        conn = sqlite3.connect(str(dbpath))
        cur = conn.cursor()
        tb_creation = "CREATE TABLE IF NOT EXISTS Conferences (\
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
        cur.execute(tb_creation)

        # TODO String formatting not foolproof, i.e. Xi'an
        cur.execute(
            'INSERT OR REPLACE INTO Conferences (title, url, timetable, year, wayback_url, categories, aux_links, persons, accessible) \
            VALUES ("{}", "{}", "{}", {}, "{}", "{}", "{}", "{}", "Unknown")'.format(
                conference['title'], conference['link'], conference['timetable'],
                conference['year'], conference['wayback_url'], conference['categories'],
                conference['aux_links'], conference['persons'])
            )

        conn.commit()
        cur.close()
        conn.close()


    @staticmethod
    def mark_accessibility(url: str, access_status: str, dbpath: str):
        print("url: {}, status: {}".format(url, access_status))
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






