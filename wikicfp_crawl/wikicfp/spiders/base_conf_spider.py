import pandas as pd
from scrapy.spiders import CrawlSpider, Request
from urllib.parse import urlparse
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError
from .classifier import URLClassifier
from .constants import CSV_FILEPATH, CSV_HEADERS

class BaseCfpSpider(CrawlSpider):

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


    def conference_page_err(self, failure):
        """
        Handles error callbacks of Requests
        """
        conference_domain = ""
        url_error = ""
        if failure.check(HttpError):
            response = failure.value.response
            conference_domain = response.url
            url_error = "HttpError: {}".format(response.status)
        else:
            request = failure.request
            conference_domain = request.url
            if failure.check(DNSLookupError):
                url_error = "DNSLookupError"
            elif failure.check(TimeoutError):
                url_error = "TimeoutError"
            else:
                url_error = "Misc. Error"

        df = pd.read_csv(CSV_FILEPATH, sep='\t', names=CSV_HEADERS)
        df.loc[df['link'] == conference_domain, 'aux_links'] = '{}'.format(url_error)
        df[1:].to_csv(CSV_FILEPATH, index=False, sep='\t')

