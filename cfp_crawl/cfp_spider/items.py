# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ConferenceItem(scrapy.Item):
    """
    Conference Item representing information as scraped from wikicfp
    """
    title = scrapy.Field()
    url = scrapy.Field()
    timetable = scrapy.Field()
    year = scrapy.Field()
    wayback_url = scrapy.Field()
    categories = scrapy.Field()
    aux_links = scrapy.Field()
    persons = scrapy.Field()
    accessible = scrapy.Field()

    @staticmethod
    def conference_to_csv(conference: 'Conference', filepath: str):
        """
        Takes a Conference object and writes to the specified filepath
        """
        with open(filepath, 'a+') as conference_csv:
            for value in conference.values():
                conference_csv.write('{}\t'.format(value))
            conference_csv.write('\n')
