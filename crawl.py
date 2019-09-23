import scrapy
from scrapy.crawler import CrawlerProcess

from cfp_crawl.config import DB_FILEPATH
from cfp_crawl.cfp_spider.utils import ConferenceHelper
from cfp_crawl.cfp_spider.spiders.all_confs_spider import ConfSeriesSpider
from cfp_crawl.cfp_spider.spiders.latest_confs_spider import LatestCfpSpider

# Create necessary DB tables
ConferenceHelper.create_db(DB_FILEPATH)

# Start crawl
process = CrawlerProcess(settings={})
process.crawl(LatestCfpSpider)
process.start()
