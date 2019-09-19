import pandas as pd
import scrapy
import urllib
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from .classifier import URLClassifier
from .config import CSV_FILEPATH, CSV_HEADERS, REQUEST_HEADERS

class BaseCfpSpider(scrapy.spiders.CrawlSpider):


    def parse_conference_page(self, response):
        """
        Parses conference homepages and determines whether found URLs are valid for further crawling
        """

        conference_domain = '{url.scheme}://{url.netloc}'.format(url=urlparse(response.url))

        # Possible further crawls from all links on homepage
        further_crawls = []
        conference_home_links = response.xpath('//a/@href')

        conference_links: List[str] = []

        # TODO Classification of links to e.g. Committee, Speakers etc.
        for link_elem in conference_home_links:
            link = link_elem.get()
            # Rectify partial links
            full_link = link if bool(urlparse(link).netloc) else "/".join([conference_domain, link])
            conference_links.append(full_link)
            URLClassifier.classify_url(full_link)

        df = pd.read_csv(CSV_FILEPATH, sep='\t', names=CSV_HEADERS)
        df.loc[df['link'] == conference_domain, 'aux_links'] = '{}'.format(conference_links)
        df[1:].to_csv(CSV_FILEPATH, index=False, sep='\t')

        return


    def process_conference_link(self, conf_url: str, wayback_url=""):
        """
        Check if conference url is accessible, if not attempts crawl from wayback machine
        """

        # Set arbitrary browser agent in header since certain sites block against crawlers
        try:
            conf_link_res = urlopen(Request(conf_url, headers=REQUEST_HEADERS))
            if conf_link_res.status == 200:
                return scrapy.spiders.Request(url=conf_url, callback=self.parse_conference_page,
                                        errback=self.conference_page_err,
                                        dont_filter=True)

        except urllib.error.HTTPError as err:
            print("HTTP Error: {}".format(err))
            return scrapy.spiders.Request(url=wayback_url, callback=self.parse_conference_page,
                                    errback=self.conference_page_err,
                                    dont_filter=True)

        except urllib.error.URLError as err:
            print("URL Error: {}".format(err))
            return scrapy.spiders.Request(url=wayback_url, callback=self.parse_conference_page,
                                    errback=self.conference_page_err,
                                    dont_filter=True)



    def conference_page_err(self, failure):
        """
        Handles error callbacks of Requests
        """
        conference_domain = ""
        url_error = repr(failure)

        # TODO Current rewriting entire csv file
        df = pd.read_csv(CSV_FILEPATH, sep='\t', names=CSV_HEADERS)
        df.loc[df['link'] == conference_domain, 'aux_links'] = '{}'.format(url_error)
        df[1:].to_csv(CSV_FILEPATH, index=False, sep='\t')

