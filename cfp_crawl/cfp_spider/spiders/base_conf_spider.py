import pandas as pd
import urllib
from urllib.request import Request, urlopen
import scrapy

from cfp_crawl.config import DOWNLOAD_DELAY, DOWNLOAD_TIMEOUT, LOG_LEVEL, DB_FILEPATH, REQUEST_HEADERS
from cfp_crawl.cfp_spider.items import ConferenceItem
from cfp_crawl.cfp_spider.wikicfp_parser import WikiConfParser
from cfp_crawl.cfp_spider.utils import ConferenceHelper

class BaseCfpSpider(scrapy.spiders.CrawlSpider):

    custom_settings = {
        'LOG_LEVEL': LOG_LEVEL,
        'DOWNLOAD_DELAY': DOWNLOAD_DELAY,
        'DOWNLOAD_TIMEOUT': DOWNLOAD_TIMEOUT
    }


    def parse_conference_page(self, response):
        """
        Parses conference homepages and determines whether found URLs are valid for further crawling
        """

        content_type = response.headers.get('content-type')
        content_type = content_type.decode('utf-8') if content_type else ''
        if 'application/pdf' in content_type:
            ConferenceHelper.mark_accessibility(response.url, "Accessible PDF", DB_FILEPATH)
        else:
            conference_domain = '{url.scheme}://{url.netloc}'.format(url=urllib.parse.urlparse(response.url))
            # Possible further crawls from all links on homepage
            further_crawls = []
            conference_home_links = response.xpath('//a/@href')

            conference_links: List[str] = []

            # TODO Classification of links to e.g. Committee, Speakers etc.
            for link_elem in conference_home_links:
                link = link_elem.get()
                # Rectify partial links
                full_link = link if bool(urllib.parse.urlparse(link).netloc) else "/".join([conference_domain, link])
                conference_links.append(full_link)

        return


    def process_wikiconf(self, response):
        """
        Process individual conference page within wikicfp
            - Parse conference page and save basic conference info to database

        Returns link of conference page to facilitate crawling
        """
        parsed_conference: ConferenceItem = WikiConfParser.parse_conf(response)
        ConferenceHelper.add_to_db(parsed_conference, DB_FILEPATH)
        url = parsed_conference['url']
        if url:
            if parsed_conference['wayback_url']:
                return self.process_conference_url(url, parsed_conference['wayback_url'])
            else:
                return self.process_conference_url(url)


    def process_conference_url(self, conf_url: str, wayback_url):
        """
        Check if conference url is accessible, if not attempts crawl from wayback machine
        """

        # Set arbitrary browser agent in header since certain sites block against crawlers
        try:
            conf_link_res = urlopen(Request(conf_url, headers=REQUEST_HEADERS))
            if conf_link_res.status == 200:
                ConferenceHelper.mark_accessibility(conf_url, "Accessible URL", DB_FILEPATH) # Mark URL accessible
                return scrapy.spiders.Request(url=conf_url, callback=self.parse_conference_page,
                                              errback=self.conf_url_error,
                                              dont_filter=True)

        except urllib.error.HTTPError as err:
            ConferenceHelper.mark_accessibility(conf_url, "HTTP Error", DB_FILEPATH)
            if wayback_url != "Not Available":
                return scrapy.spiders.Request(url=wayback_url, callback=self.parse_conference_page,
                                              errback=self.conf_url_error,
                                              dont_filter=True)

        except urllib.error.URLError as err:
            ConferenceHelper.mark_accessibility(conf_url, "URL Error", DB_FILEPATH)
            if wayback_url != "Not Available":
                return scrapy.spiders.Request(url=wayback_url, callback=self.parse_conference_page,
                                              errback=self.conf_url_error,
                                              dont_filter=True)
        except Exception as err:
            ConferenceHelper.mark_accessibility(conf_url, "Certificate Error", DB_FILEPATH)
            if wayback_url != "Not Available":
                return scrapy.spiders.Request(url=wayback_url, callback=self.parse_conference_page,
                                              errback=self.conf_url_error,
                                              dont_filter=True)



    def conf_url_error(self, failure):
        """
        Catch all for conference url error
        """
        print("==============================")
        print("Errback from Request")
        print(repr(failure))
        print("==============================")

