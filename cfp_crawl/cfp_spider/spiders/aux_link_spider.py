import scrapy
import sqlite3
from scrapy.spiders import CrawlSpider, Request

from cfp_crawl.cfp_spider.utils import ConferenceHelper
from cfp_crawl.classifier import classify_link, URLClass
from cfp_crawl.config import crawl_settings, DB_FILEPATH, REQUEST_HEADERS

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


class AuxLinkSpider(scrapy.spiders.CrawlSpider):

    name = "aux"
    custom_settings = {
        'LOG_LEVEL': 'ERROR',
        'DOWNLOAD_DELAY': 1
    }

    def __init__(self):
        super(AuxLinkSpider, self).__init__()
        self.start_requests()


    def start_requests(self):
        for row_id, conf_id, url in self.get_start_urls(DB_FILEPATH):
            yield Request(url=url, dont_filter=True,
                meta={'url_id': row_id, 'conf_id': conf_id},
                callback=self.parse, errback=self.parse_error)


    def get_start_urls(self, dbpath: str) -> 'Tuple':
        """
        Get all auxiliary URLs from database
        """
        conn = sqlite3.connect(str(dbpath))
        cur = conn.cursor()
        urls = cur.execute("SELECT * FROM Urls").fetchall()
        cur.close()
        conn.close()
        return [t for t in urls]


    def parse(self, response):
        # Check for content type skip for pdf for now
        content_type = response.headers.get('content-type')
        content_type = content_type.decode('utf-8') if content_type else ''
        if 'application/pdf' in content_type:
            return

        nodes = get_children(0, response.xpath("body")[0])
        for node in nodes:
            node = (response.request.meta['url_id'], *node)
            ConferenceHelper.add_line_db(node, DB_FILEPATH)
        return


    def parse_error(self, error):
        print("============================")
        print(error.request.meta['conf_id'])
        print(error.request.url)
        print("============================")
