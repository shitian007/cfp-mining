import re
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from .utils import ConfParser

class LatestCfpSpider(CrawlSpider):
    name = 'latest'
    allowed_domains = ['wikicfp.com']
    start_urls = ['http://www.wikicfp.com/cfp/allcfp']
    num_conf_crawled = 0

    custom_settings = {
        'DOWNLOAD_DELAY': '0.5',
    }

    rules = (
        # Traverse all pages
        Rule(LinkExtractor(allow='cfp/allcfp'), callback='parse_item', follow=True),
        # Individual Conference page on wikicfp
        Rule(LinkExtractor(allow='cfp/servlet/event.showcfp'), callback='parse_item'),
    )


    def parse_item(self, response):
        if re.search('cfp/servlet/event.showcfp', response.url):
            self.num_conf_crawled += 1
            print(self.num_conf_crawled)
        ConfParser.parse_item(response)
