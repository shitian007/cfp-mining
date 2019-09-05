import pandas as pd
from scrapy.spiders import CrawlSpider
from urllib.parse import urlparse
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
