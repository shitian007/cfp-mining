import argparse
import scrapy
from scrapy.crawler import CrawlerProcess

from cfp_crawl.config import DB_FILEPATH, CRAWL_FILEPATH
from cfp_crawl.cfp_spider.utils import ConferenceHelper
from cfp_crawl.cfp_spider.spiders.base_conf_spider import BaseCfpSpider
from cfp_crawl.cfp_spider.spiders.all_confs_spider import ConfSeriesSpider
from cfp_crawl.cfp_spider.spiders.latest_confs_spider import LatestCfpSpider
from cfp_crawl.cfp_spider.spiders.aux_link_spider import AuxLinkSpider

class TestSpider(BaseCfpSpider):

    name = "test"
    domain_name = "http://web.archive.org"
    start_urls = ["http://www.risc.uni-linz.ac.at/conferences/ab2008"]

    def parse(self, response):
        yield self.process_conference_url(response.url, 1, "Not Available")

parser = argparse.ArgumentParser(description='')
parser.add_argument('crawler', type=str, help="Specifies crawler type")
args = parser.parse_args()
crawl_type = args.crawler

# Start crawl
process = CrawlerProcess(settings={})
if crawl_type == 'test':
    process.crawl(TestSpider)
    process.start()
elif crawl_type == 'aux':
    process.crawl(AuxLinkSpider)
    process.start()
elif crawl_type == 'all':
    # Create necessary DB tables
    ConferenceHelper.create_db(DB_FILEPATH)
    process.crawl(ConfSeriesSpider)
    process.start()
else:
    print("Unspecified crawl type")
