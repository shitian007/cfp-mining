import argparse
import scrapy
from scrapy.crawler import CrawlerProcess

from cfp_crawl.config import DB_FILEPATH, CRAWL_FILEPATH
from cfp_crawl.cfp_spider.database_helper import DatabaseHelper
from cfp_crawl.cfp_spider.spiders.base_wikicfp_spider import BaseCfpSpider
from cfp_crawl.cfp_spider.spiders.wikicfp_all_spider import WikicfpAllSpider
from cfp_crawl.cfp_spider.spiders.wikicfp_latest_spider import WikicfpLatestSpider
from cfp_crawl.cfp_spider.spiders.conf_crawl import ConferenceCrawlSpider


class TestSpider(BaseCfpSpider):

    name = "test"
    domain_name = "http://web.archive.org"
    start_urls = [""]

    def parse(self, response):
        yield self.process_conference_url(response.url, 1, "Not Available")

DatabaseHelper.create_db(DB_FILEPATH)
parser = argparse.ArgumentParser(description='')
parser.add_argument('crawler', type=str, help="Specifies crawler type")
args = parser.parse_args()
crawl_type = args.crawler

# Start crawl
process = CrawlerProcess(settings={})
spider_type = {
    'wikicfp_all': WikicfpAllSpider,
    'wikicfp_latest': WikicfpLatestSpider,
    'conf_crawl': ConferenceCrawlSpider,
    'test': TestSpider
}
if crawl_type not in spider_type.keys():
    print("Unspecified crawl type")
    print("Usage:\n\t python crawl <crawler_type>\n\t\
        'wikicfp_all': WikicfpAllSpider\n\t\
        'wikicfp_latest': WikicfpLatestSpider\n\t\
        'conf_crawl': ConferenceCrawlSpider\n\t\
        'test': TestSpider"\
    )

else:
    if crawl_type == 'wikicfp_all' or crawl_type == 'wikicfp_latest':
        DatabaseHelper.create_db(DB_FILEPATH)  # Create necessary DB tables
    process.crawl(spider_type[crawl_type])
    process.start()
