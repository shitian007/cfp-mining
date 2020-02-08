import re
import string
import unicodedata

def clean_punctuation(ltext: str):
    ltext = ltext.strip(string.punctuation) # Strip leading and trailing punctuation
    ltext = unicodedata.normalize("NFKD", ltext) # Normalize string to unicoded to remove splitting errors
    ltext = re.sub('\t|\r|\n|\(|\)|\"|\'', ' ', ltext) # Replace tabs and newlines with spaces
    ltext = re.sub(' +', ' ', ltext) # Remove multiple spacing
    ltext = ltext.strip()
    return ltext

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