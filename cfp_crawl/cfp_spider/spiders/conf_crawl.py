import scrapy
import sqlite3
import urllib
from typing import List, Tuple
from scrapy.spiders import CrawlSpider, Request

from cfp_crawl.cfp_spider.items import ConferencePage
from cfp_crawl.cfp_spider.database_helper import DatabaseHelper
from cfp_crawl.cfp_spider.spiders.utils import get_content_type, get_relevant_links, get_url_status
from cfp_crawl.config import crawl_settings, DB_FILEPATH, REQUEST_HEADERS


class ConferenceCrawlSpider(scrapy.spiders.CrawlSpider):
    """
    Retrieves urls from `WikicfpConferences` table and crawls each Conference homepage
    """

    name = "confcrawl"
    custom_settings = crawl_settings

    def __init__(self):
        super(ConferenceCrawlSpider, self).__init__()
        self.start_requests()

    def start_requests(self):
        """
        Get all Conference Homepage URLs from database and yields scrapy Requests
        """
        conn = sqlite3.connect(str(DB_FILEPATH))
        cur = conn.cursor()
        confs = cur.execute(
            "SELECT * FROM WikicfpConferences WHERE crawled='No'").fetchall()
        cur.close()
        conn.close()
        for conf in confs:
            conf_id, url, wayback_url, accessibility = conf[0], conf[3], conf[6], conf[8]
            access_url = url if accessibility == "Accessible URL" else wayback_url
            if access_url != "Not Available":  # Wayback ULR might be `Not Available`
                yield Request(url=access_url, dont_filter=True,
                              meta={'conf_id': conf_id},
                              callback=self.parse,
                              errback=self.parse_page_error)

    def parse(self, response):
        """
        Parses conference homepage and determines whether found URLs are valid for further crawling
        """
        conf_id = response.meta['conf_id']
        content_type = get_content_type(response)
        DatabaseHelper.mark_crawled(conf_id, DB_FILEPATH)
        self.add_conf_page(conf_id, response)
        if content_type != 'pdf':
            # Crawl relevant links
            for link in get_relevant_links(response):
                if get_url_status(link) != 200:
                    DatabaseHelper.add_page(
                        ConferencePage(conf_id=conf_id, url=link, html="",
                                       content_type="Inaccessible"), DB_FILEPATH)
                else:
                    yield Request(url=link, dont_filter=True, meta={'conf_id': conf_id},
                                  callback=self.parse_aux_conf_page,
                                  errback=self.parse_page_error)

    def parse_aux_conf_page(self, response):
        """
        Parses auxiliary conference pages
        """
        conf_id = response.request.meta['conf_id']
        content_type = get_content_type(response)
        self.add_conf_page(conf_id, response)

    def add_conf_page(self, conf_id: int, response: 'Response'):
        """
        Adds Conference Page to database
        """
        content_type = get_content_type(response)
        if content_type == 'pdf':
            page_id = DatabaseHelper.add_page(
                ConferencePage(conf_id=conf_id, url=response.url, html="",
                               content_type=content_type, processed="No"), DB_FILEPATH)
        else:
            page_html = response.xpath("//html").get()
            # Add Conference Homepage to database
            page_id = DatabaseHelper.add_page(
                ConferencePage(conf_id=conf_id, url=response.url, html=page_html,
                               content_type=content_type, processed="No"), DB_FILEPATH)

    def parse_page_error(self, error):
        print("============================")
        print("Error processing:")
        print(error.request.meta['conf_id'])
        print(error.request.url)
        print("============================")
