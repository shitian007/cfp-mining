import pandas as pd
import urllib
import scrapy

from cfp_crawl.classifier import classify_link, URLClass
from cfp_crawl.config import crawl_settings, DB_FILEPATH
from cfp_crawl.cfp_spider.items import WikiConferenceItem
from cfp_crawl.cfp_spider.database_helper import DatabaseHelper
from cfp_crawl.cfp_spider.spiders.utils import get_url_status
from cfp_crawl.cfp_spider.spiders.wikicfp_parser import WikiConfParser


class BaseCfpSpider(scrapy.spiders.CrawlSpider):

    custom_settings = crawl_settings

    def process_wikiconf(self, response):
        """
        Process individual conference page within wikicfp
            - Parse conference page and save basic conference info to database

        Returns link of conference page to facilitate crawling
        """
        parsed_conference: WikiConferenceItem = WikiConfParser.parse_conf(response)
        row_id = DatabaseHelper.add_wikicfp_conf(parsed_conference, DB_FILEPATH)
        url = parsed_conference['url']
        if url:  # Check accessibilty of both direct URL and WaybackMachine URL
            return self.process_conference_url(url, row_id, parsed_conference['wayback_url'])

    def process_conference_url(self, conf_url: str, row_id: int, wayback_url):
        """
        Check if conference url is accessible, else checks availability on Waybackmachine Archive
        """
        # Metadata in case of request error
        meta = {
            'wayback_url': wayback_url,
            'row_id': row_id
        }
        # Set arbitrary browser agent in header since certain sites block against crawlers
        try:
            if get_url_status(conf_url) == 200:
                DatabaseHelper.mark_accessibility(
                    conf_url, "Accessible URL", DB_FILEPATH)  # Mark URL accessible
        except Exception as e:
            if e.__class__ == urllib.error.HTTPError:
                DatabaseHelper.mark_accessibility(
                    conf_url, "HTTP Error", DB_FILEPATH)
            elif e.__class__ == urllib.error.URLError:
                DatabaseHelper.mark_accessibility(
                    conf_url, "HTTP Error", DB_FILEPATH)
            else:
                DatabaseHelper.mark_accessibility(
                    conf_url, "Certificate Error", DB_FILEPATH)

    def handle_request_error(self, err):
        """
        Catchall for Conference Homepage Url Error
        """
        print("===============================================")
        if "wayback" in err.request.url:
            print("Fail on wayback")
        print("fail on {}".format(repr(err)))
        print("url: {}".format(err.request.url))
        print("wayback: {}".format(err.request.meta['wayback_url']))
        print("===============================================")
        DatabaseHelper.mark_accessibility(
            err.request.url, "Crawler Access Error", DB_FILEPATH)
        meta = err.request.meta
        if "wayback" not in err.request.url and "Errback" not in meta:
            meta['Errback'] = True
            return scrapy.spiders.Request(url=meta['wayback_url'], dont_filter=True, meta=meta,
                                          callback=self.parse_conference_page,
                                          errback=self.handle_request_error)
