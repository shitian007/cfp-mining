import pandas as pd
import urllib
from urllib.request import Request, urlopen
import scrapy

from cfp_crawl.classifier import classify_link, URLClass
from cfp_crawl.config import DOWNLOAD_DELAY, DOWNLOAD_TIMEOUT, LOG_LEVEL, CRAWL_FILEPATH, LOG_FILEPATH, DB_FILEPATH, REQUEST_HEADERS
from cfp_crawl.cfp_spider.items import ConferenceItem
from cfp_crawl.cfp_spider.utils import ConferenceHelper
from cfp_crawl.cfp_spider.wikicfp_parser import WikiConfParser


class BaseCfpSpider(scrapy.spiders.CrawlSpider):

    custom_settings = {
        'LOG_LEVEL': LOG_LEVEL,
        'DOWNLOAD_DELAY': DOWNLOAD_DELAY,
        'DOWNLOAD_TIMEOUT': DOWNLOAD_TIMEOUT,
        'LOG_FILE': LOG_FILEPATH,
        'JOBDIR': CRAWL_FILEPATH
    }

    def parse_conference_page(self, response):
        """
        Parses conference homepages and determines whether found URLs are valid for further crawling
        """
        content_type = response.headers.get('content-type')
        content_type = content_type.decode('utf-8') if content_type else ''
        if "Errback" in response.request.meta:
            print("----- From Errback ------")
        if 'application/pdf' in content_type:
            ConferenceHelper.mark_accessibility( response.url, "Accessible PDF", DB_FILEPATH)
        else:
            conf_row_id = response.request.meta['row_id']
            # TODO This is different for wayback
            conference_domain = '{url.scheme}://{url.netloc}'.format(url=urllib.parse.urlparse(response.url))
            if "web.archive.org" in conference_domain:
                return

            conference_home_links = response.xpath('//a')
            auxiliary_urls: List[str] = []
            # Classify URL class
            for link_selector in conference_home_links:
                link = link_selector.xpath('@href').get()
                link = link if link else ""
                # Rectify partial links
                full_link = link if bool(urllib.parse.urlparse(link).netloc) else "/".join([conference_domain, link])

                url_class = classify_link(link_selector)
                if url_class != URLClass.UNKNOWN:
                    auxiliary_urls.append(full_link)
                    ConferenceHelper.add_url_db( full_link, conf_row_id, DB_FILEPATH)
        return


    def process_wikiconf(self, response):
        """
        Process individual conference page within wikicfp
            - Parse conference page and save basic conference info to database

        Returns link of conference page to facilitate crawling
        """
        parsed_conference: ConferenceItem = WikiConfParser.parse_conf(response)
        row_id = ConferenceHelper.add_conf_db(parsed_conference, DB_FILEPATH)
        url = parsed_conference['url']
        if url:
            return self.process_conference_url(url, row_id, parsed_conference['wayback_url'])


    def process_conference_url(self, conf_url: str, row_id: int, wayback_url):
        """
        Check if conference url is accessible, if not attempts crawl from wayback machine
        """

        # Metadata in case of request error
        meta = {
            'wayback_url': wayback_url,
            'row_id': row_id
        }
        # Set arbitrary browser agent in header since certain sites block against crawlers
        try:
            conf_link_res = urlopen(Request(conf_url, headers=REQUEST_HEADERS))
            if conf_link_res.status == 200:
                ConferenceHelper.mark_accessibility(
                    conf_url, "Accessible URL", DB_FILEPATH)  # Mark URL accessible
                return scrapy.spiders.Request(url=conf_url, dont_filter=True, meta=meta,
                                              callback=self.parse_conference_page,
                                              errback=self.handle_request_error)
        except Exception as e:
            if e.__class__ == urllib.error.HTTPError:
                ConferenceHelper.mark_accessibility(conf_url, "HTTP Error", DB_FILEPATH)
            elif e.__class__ == urllib.error.URLError:
                ConferenceHelper.mark_accessibility(conf_url, "HTTP Error", DB_FILEPATH)
            else:
                ConferenceHelper.mark_accessibility(conf_url, "Certificate Error", DB_FILEPATH)
            if wayback_url != "Not Available":
                return scrapy.spiders.Request(url=wayback_url, dont_filter=True, meta=meta,
                                              callback=self.parse_conference_page,
                                              errback=self.handle_request_error)


    def handle_request_error(self, err):
        """
        Catch all for conference url error
        """
        print("===============================================")
        if "wayback" in err.request.url:
            print("Fail on wayback")
        print("fail on {}".format(repr(err)))
        print("url: {}".format(err.request.url))
        print("wayback: {}".format(err.request.meta['wayback_url']))
        print("===============================================")
        ConferenceHelper.mark_accessibility(err.request.url, "Crawler Access Error", DB_FILEPATH)
        meta = err.request.meta
        if "wayback" not in err.request.url and "Errback" not in meta:
            meta['Errback'] = True
            return scrapy.spiders.Request(url=meta['wayback_url'], dont_filter=True, meta=meta,
                                          callback=self.parse_conference_page,
                                          errback=self.handle_request_error)
