import re
import string
import unicodedata


def clean_punctuation(ltext: str):
    # Strip leading and trailing punctuation
    ltext = ltext.strip(string.punctuation)
    # Normalize string to unicoded to remove splitting errors
    ltext = unicodedata.normalize("NFKD", ltext)
    # Replace tabs and newlines with spaces
    ltext = re.sub('\t|\r|\n|\(|\)|\"|\'', ' ', ltext)
    ltext = re.sub(' +', ' ', ltext)  # Remove multiple spacing
    ltext = ltext.strip()
    return ltext


class DatabaseHelper:

    @staticmethod
    def create_tables(cnx):
        """Create tables for consolidated Person/Org/Conf

        Args:
            cnx (sqlite3.Cursor): Connection to database
        """
        cur = cnx.cursor()
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
                crawled TEXT);")

        cur.execute("CREATE TABLE IF NOT EXISTS ConferencePages (\
                    id INTEGER NOT NULL PRIMARY KEY,\
                    conf_id INTEGER NOT NULL REFERENCES Urls(id),\
                    url TEXT NOT NULL UNIQUE,\
                    content_type TEXT,\
                    processed TEXT);")

        cur.execute("CREATE TABLE IF NOT EXISTS Organizations (\
                    id INTEGER NOT NULL PRIMARY KEY, name TEXT UNIQUE);")

        cur.execute("CREATE TABLE IF NOT EXISTS Persons (\
                    id INTEGER NOT NULL PRIMARY KEY, name TEXT,\
                    org_id REFERENCES Organizations(id),\
                    orcid TEXT, gscholar_id TEXT, aminer_id TEXT,\
                    CONSTRAINT p_o UNIQUE(name, org_id)\
                    );")

        cur.execute("CREATE TABLE IF NOT EXISTS PersonRole(\
            role_id INTEGER PRIMARY KEY NOT NULL,\
            role_type TEXT NOT NULL,\
            conf_id INTEGER REFERENCES WikicfpConferences(id),\
            person_id INTEGER REFERENCES Persons(id),\
            CONSTRAINT u_p_c_role UNIQUE(person_id, conf_id, role_type)\
            );")

        cnx.commit()

    @staticmethod
    def get_persons_info(cur, conf_id):
        return cur.execute("SELECT p.name, o.name, pr.role_type FROM Persons p\
            JOIN PersonOrganization po ON po.person_id=p.id\
            JOIN Organizations o ON po.org_id=o.id\
            JOIN PersonRole pr ON pr.person_id=p.id\
            WHERE pr.conf_id=?", (conf_id,)).fetchall()
