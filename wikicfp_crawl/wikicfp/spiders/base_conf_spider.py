import pandas as pd
import scrapy
import urllib
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from .utils import Conference
from .config import DB_FILEPATH, REQUEST_HEADERS

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

        return


    def process_conference_link(self, conf_url: str, wayback_url):
        """
        Check if conference url is accessible, if not attempts crawl from wayback machine
        """

        # Set arbitrary browser agent in header since certain sites block against crawlers
        try:
            conf_link_res = urlopen(Request(conf_url, headers=REQUEST_HEADERS))
            if conf_link_res.status == 200:
                Conference.mark_accessibility(conf_url, "Accessible URL", DB_FILEPATH) # Mark URL accessible
                return scrapy.spiders.Request(url=conf_url, callback=self.parse_conference_page,
                                        errback=self.conference_page_err,
                                        dont_filter=True)

        except urllib.error.HTTPError as err:
            Conference.mark_accessibility(conf_url, "HTTP Error", DB_FILEPATH)
            if wayback_url != "Not Available":
                return scrapy.spiders.Request(url=wayback_url, callback=self.parse_conference_page,
                                        errback=self.conference_page_err,
                                        dont_filter=True)

        except urllib.error.URLError as err:
            Conference.mark_accessibility(conf_url, "URL Error", DB_FILEPATH)
            if wayback_url != "Not Available":
                return scrapy.spiders.Request(url=wayback_url, callback=self.parse_conference_page,
                                        errback=self.conference_page_err,
                                        dont_filter=True)
