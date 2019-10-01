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
speakers = 'speaker[a-z]*|tutorial|workshop'
admin = 'date|schedule|loca[a-z]+'

def classify_url(url: str):
    """
    Classifies url
    """
    parsed_url: 'ParseResult' = urlparse(url)
    domain = parsed_url.netloc
    # Take only path and query, lowercase
    cleaned_url: str = re.sub(r'html', '', '{url.path}#{url.query}'.format(url=parsed_url)).lower()
    if re.search(org, cleaned_url):
        return URLClass.COMMITTEE
    elif re.search(speakers, cleaned_url):
        return URLClass.SPEAKERS
    elif re.search(speakers, cleaned_url):
        return URLClass.ADMINISTRATIVE
    else:
        return URLClass.UNKNOWN

