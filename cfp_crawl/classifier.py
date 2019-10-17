import re
from typing import List
from urllib.parse import urlparse

class URLClass:
    COMMITTEE = 'org'
    SPEAKERS = 'speakers'
    ADMINISTRATIVE = 'admin'
    UNKNOWN = 'unk'


# Regex string representations of possible keywords
org = 'organiz[a-z]+|committee[a-z]*|prog[a-z]*'
speakers = 'author[s]*|speaker[a-z]*|tutorial|workshop'
admin = 'date|schedule|loca[a-z]+'

def classify_link(link: 'Selector'):
    """
    Takes a xpath Selector and classifies link based on both URL and text
    """
    url = link.xpath('@href').get()
    url = url.lower() if url else ""
    text = link.xpath('text()').get()
    text = text.lower() if text else ""
    if re.search(org, url) or re.search(org, text):
        return URLClass.COMMITTEE
    elif re.search(speakers, url) or re.search(speakers, text):
        return URLClass.SPEAKERS
    elif re.search(admin, url) or re.search(admin, text):
        return URLClass.ADMINISTRATIVE
    else:
        return URLClass.UNKNOWN

