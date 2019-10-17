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

# Start crawl
process = CrawlerProcess(settings={})
TEST = False
AUX = False
if TEST:
    process.crawl(TestSpider)
elif AUX:
    process.crawl(AuxLinkSpider)
else:
    # Create necessary DB tables
    ConferenceHelper.create_db(DB_FILEPATH)
    process.crawl(ConfSeriesSpider)
process.start()
