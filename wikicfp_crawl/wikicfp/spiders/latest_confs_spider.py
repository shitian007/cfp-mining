import re
import scrapy
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from .base_conf_spider import BaseCfpSpider
from .wikicfp_conf_parser import WikiConfParser
from .config import DOWNLOAD_DELAY, DOWNLOAD_TIMEOUT


class LatestCfpSpider(BaseCfpSpider):
    name = 'latest'
    # allowed_domains = ['wikicfp.com']
    start_urls = ['http://www.wikicfp.com/cfp/allcfp']
    num_conf_crawled = 0

    custom_settings = {
        'DOWNLOAD_DELAY': DOWNLOAD_DELAY,
    }

    rules = (
        # Traverse all pages
        Rule(LinkExtractor(allow='cfp/allcfp'), callback='parse_wikicfp_page', follow=True),
        # Individual Conference page on wikicfp
        Rule(LinkExtractor(allow='cfp/servlet/event.showcfp'), callback='parse_wikicfp_page'),
    )


    def parse_wikicfp_page(self, response):
        """
        Parses Conferences on wikicfp domain and follow links to actual conference page if link exists
        """
        # Processing of individual CFP page within wikicfp
        if re.search('cfp/servlet/event.showcfp', response.url):  # Conference page
            self.num_conf_crawled += 1

            parsed_conference: 'Conference' = WikiConfParser.parse_conf(response)
            link = parsed_conference['link']
            # Certain conferences might not contain links
            if link:
                yield scrapy.Request(url=link,
                                     callback=self.parse_conference_page,
                                     errback=self.conference_page_err)


