import re
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from .wikicfp_conf_parser import WikiConfParser
from .constants import DOWNLOAD_DELAY

class LatestCfpSpider(CrawlSpider):
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

        # Processing of individual CFP page within wikicfp
        if re.search('cfp/servlet/event.showcfp', response.url): # Conference page
            self.num_conf_crawled += 1

            parsed_conference: 'Conference' = WikiConfParser.parse_conf(response)
            link = parsed_conference['link']
            if link:
                yield scrapy.Request(url=link, callback=self.parse_conference_page)


    def parse_conference_page(self, response):

        # TODO Crawl conference domains on another spider
        conference_domain = response.url # Assume link to root

        # Possible further crawls
        further_crawls = []

        conference_home_links = response.xpath('//a/@href')

        # TODO Classification of links to e.g. Committee, Speakers etc.
        for link_elem in conference_home_links:
            link = link_elem.get()
            if re.search('committee', link):
                yield scrapy.Request(link if re.search(conference_domain, link) else "/".join([conference_domain, link]), callback=self.parse_aux)
                further_crawls.append(
                    link if re.search(conference_domain, link)
                    else "/".join([conference_domain, link]))

        return


    def parse_aux(self, response):
        print("======= Possible Committee Page of Conference =========")
        print("URL: {}".format(response.url))
        text = response.xpath('//body//text()').extract()
        return
