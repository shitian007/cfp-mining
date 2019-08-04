import re
import scrapy
from scrapy import Spider, Request
from .conf_parser import ConfParser

class ConfSeriesSpider(Spider):
    domain_name = 'http://www.wikicfp.com'
    name = 'conf'
    allowed_domains = ['wikicfp.com']
    start_urls = ['http://www.wikicfp.com/cfp/series?t=c&i=A']
    num_pages_crawls = 0

    custom_settings = {
        'DOWNLOAD_DELAY': 5
    }

    def parse(self, response):
        if re.search('cfp/servlet/event.showcfp', response.url):
            ConfParser.parse_item(response)
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


