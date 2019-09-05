import re
import scrapy
from scrapy import Request
from .base_conf_spider import BaseCfpSpider
from .wikicfp_conf_parser import WikiConfParser
from .constants import DOWNLOAD_DELAY

class ConfSeriesSpider(BaseCfpSpider):
    domain_name = 'http://www.wikicfp.com'
    name = 'all'
    start_urls = ['http://www.wikicfp.com/cfp/series?t=c&i=A']
    num_pages_crawls = 0

    custom_settings = {
        'DOWNLOAD_DELAY': DOWNLOAD_DELAY
    }

    def parse(self, response):
        """
        Parses pages starting from page A of Conference Series pages
          - cfp/series: Consolidation of multiple programs
          - cfp/program: Singular program possibly containing CFPs
        """
        if re.search('cfp/servlet/event.showcfp', response.url):
            parsed_conference: 'Conference' = WikiConfParser.parse_conf(response)
            link = parsed_conference['link']
            if link:
                yield scrapy.Request(url=link, callback=self.parse_conference_page)
        else:
            table_main = response.xpath('//div[contains(@class, "contsec")]/center/table')

            if re.search('cfp/series', response.url): # List of series

                series_links_row = table_main.xpath('./tr//tr')[2]
                series_links = series_links_row.xpath('.//a')
                for link in series_links:
                    link_url = link.xpath('./@href').get()
                    yield Request("".join([self.domain_name, link_url]))

                program_link_rows = table_main.xpath('./tr')[2].xpath('.//tr')
                for program_link in program_link_rows:
                    program_url = program_link.xpath('.//a/@href').get()
                    yield Request("".join([self.domain_name, program_url]))

            elif re.search('cfp/program', response.url): # Program
                program_table = table_main.xpath('./tr/td[contains(@align, "center")]')[1]
                conf_links = program_table.xpath('.//a')
                for conf_link in conf_links:
                    conf_url = conf_link.xpath('./@href').get()
                    yield Request("".join([self.domain_name, conf_url]))
            else:
                pass


