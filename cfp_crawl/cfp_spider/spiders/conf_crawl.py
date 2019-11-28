import scrapy
import sqlite3
import urllib
from typing import List, Tuple
from scrapy.spiders import CrawlSpider, Request

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
        confs = cur.execute("SELECT * FROM WikicfpConferences").fetchall()
        cur.close()
        conn.close()
        for conf in confs:
            conf_id, url, wayback_url, accessibility = conf[0], conf[3], conf[6], conf[8]
            access_url = url if accessibility == "Accessible URL" else wayback_url
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
        if content_type == 'pdf':
            page_id = DatabaseHelper.add_page(
                (conf_id, response.url, "", content_type), DB_FILEPATH)
        else:
            page_html = response.xpath("//html").get()
            # Add Conference Homepage to database
            page_id = DatabaseHelper.add_page(
                (conf_id, response.url, page_html, content_type), DB_FILEPATH)
            # Add page lines
            for line in self.get_page_lines(response):
                db_line = (page_id, *line)
                DatabaseHelper.add_line(db_line, DB_FILEPATH)
            # Crawl relevant links
            for link in get_relevant_links(response):
                if get_url_status(link) != 200:
                    DatabaseHelper.add_page(
                        (conf_id, link, "", "Inaccessible"), DB_FILEPATH)
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
        if content_type == 'pdf':
            page_id = DatabaseHelper.add_page(
                (conf_id, response.url, "", content_type), DB_FILEPATH)
        else:
            page_html = response.xpath("//html").get()
            # Add Conference Page to database
            page_id = DatabaseHelper.add_page(
                (conf_id, response.url, page_html, content_type), DB_FILEPATH)
            # Add page lines
            for line in self.get_page_lines(response):
                db_line = (page_id, *line)
                DatabaseHelper.add_line(db_line, DB_FILEPATH)

    def parse_page_error(self, error):
        print("============================")
        print("Error processing:")
        print(error.request.meta['conf_id'])
        print(error.request.url)
        print("============================")

    def get_page_lines(self, response: 'Response'):
        """
        Get all lines of each conference page
        """
        def get_children(indentation: int, node: 'Selector'):
            """
            Given root node, recursively inspects children for those containing text
            and returns them with their corresponding indentation levels
            """
            nodes = []
            if node.xpath("text()").get():
                node_tag = node.xpath("name()").get()
                node_text = node.xpath("text()").get().strip()
                # Ensure node has text and is not script
                if node_text.strip() and node_tag != "script":
                    nodes.append((node_text, node_tag, indentation))
            children = node.xpath("./*")
            for child in children:
                nodes += get_children(indentation + 1, child)
            return nodes

        # TODO Handle Javascript injection of webpage content
        try:
            nodes: List[Tuple] = get_children(
                indentation=0, node=response.xpath("body")[0])
            return nodes
        except:
            return []
