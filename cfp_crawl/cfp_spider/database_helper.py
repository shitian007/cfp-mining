import sqlite3
from typing import List


class DatabaseHelper:
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
        cur.execute("CREATE TABLE IF NOT EXISTS WikicfpConferences (\
            id INTEGER NOT NULL PRIMARY KEY,\
            series TEXT NOT NULL,\
            title TEXT NOT NULL UNIQUE,\
            url TEXT,\
            timetable TEXT,\
            year INTEGER,\
            wayback_url TEXT,\
            categories TEXT,\
            accessible TEXT,\
            crawled TEXT\
        );")

        cur.execute("CREATE TABLE IF NOT EXISTS ConferencePages (\
            id INTEGER NOT NULL PRIMARY KEY,\
            conf_id INTEGER NOT NULL REFERENCES Urls(id),\
            url TEXT NOT NULL UNIQUE,\
            html TEXT,\
            content_type TEXT,\
            processed TEXT\
        );")

        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def add_wikicfp_conf(conference: 'WikiConferenceItem', dbpath: str):
        """
        Adds Conference information scraped from wikicfp
        """
        conn = sqlite3.connect(str(dbpath))
        cur = conn.cursor()
        # TODO String formatting not foolproof, i.e. Xi'an
        cur.execute(
            "INSERT OR REPLACE INTO WikicfpConferences\
            (series, title, url, timetable, year, wayback_url, categories, accessible, crawled) \
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(conference['series']),
                str(conference['title']),
                str(conference['url']),
                str(conference['timetable']),
                str(conference['year']),
                str(conference['wayback_url']),
                str(conference['categories']),
                str(conference['accessible']),
                str(conference['crawled'])
            )
        )
        conf_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()
        return conf_id

    @staticmethod
    def mark_accessibility(conf_id: int, access_status: str, dbpath: str):
        """
        Marks the accessibility attribute of a Conference url retrieved from wikicfp
        """
        conn = sqlite3.connect(str(dbpath))
        cur = conn.cursor()
        cur.execute(
            'UPDATE WikicfpConferences SET accessible = "{}" WHERE id = "{}"'.format(
                access_status, conf_id)
        )
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def mark_crawled(conf_id: int, dbpath: str):
        conn = sqlite3.connect(str(dbpath))
        cur = conn.cursor()
        cur.execute(
            'UPDATE WikicfpConferences SET crawled = "{}" WHERE id = "{}"'.format(
                'Yes', conf_id)
        )
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def add_page(conference_page: 'ConferencePageItem', dbpath: str):
        """
        Adds page of Conference
        """
        conn = sqlite3.connect(str(dbpath))
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO ConferencePages\
            (conf_id, url, html, content_type)\
            VALUES (?, ?, ?, ?)",
            (
                str(conference_page['conf_id']),
                str(conference_page['url']),
                str(conference_page['html']),
                str(conference_page['content_type'])
            )
        )
        page_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()
        return page_id
