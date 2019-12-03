import re
from urllib.request import Request, urlopen
from urllib.parse import urlparse, urljoin

from cfp_crawl.config import REQUEST_HEADERS
from cfp_crawl.url_classifier import classify_link, URLClass


def get_content_type(response: 'Response'):
    """
    Get content type of Url
    """
    content_type = response.headers.get('content-type')
    content_type = content_type.decode('utf-8') if content_type else ''
    content_type = 'pdf' if 'application/pdf' in content_type else 'html'
    return content_type


def get_url_status(url: str):
    """
    Get response status code for url
    """
    conf_link_res = urlopen(Request(url, headers=REQUEST_HEADERS))
    return conf_link_res.status


def get_relevant_links(response: 'Response'):
    """
    Retrieves the relevant links from a Conference Homepage
    """
    conference_domain = '{url.scheme}://{url.netloc}'.format(
        url=urlparse(response.url))

    relevant_links = []
    for link_selector in response.xpath('//*[@href]'):
        link = link_selector.xpath('@href').get()
        link = link if link else ""

        # Only retrieve links on the same domain
        if same_domain(response.url, link):
            # Rectify if partial links
            full_link = urljoin(response.url, link)
            url_class = classify_link(link_selector)
            if url_class != URLClass.UNKNOWN:
                relevant_links.append(full_link)

    return relevant_links


def same_domain(conf_home: str, aux_link: str):
    """
    Checks if two urls are from the same domain
        - Handles diff/same domains for Wayback as well
    """
    WAYBACK_DOMAIN = 'http://web.archive.org'
    conf_home_domain = urlparse(conf_home).netloc
    aux_link_domain = urlparse(aux_link).netloc
    if WAYBACK_DOMAIN in conf_home_domain:  # Compare for wayback
        # Get split result of /web/.../
        actual_conf_url = re.split('\/web\/[0-9]*\/', conf_home)[1]
        actual_aux_link_url = re.split('\/web\/[0-9]*\/', aux_link)[1]
        actual_conf_domain = urlparse(actual_conf_url)
        actual_aux_link_domain = urlparse(actual_aux_link_url)
        return not actual_aux_link_domain or actual_conf_domain == actual_aux_link_domain
    else:  # Normal comparison
        return not aux_link_domain or conf_home_domain == aux_link_domain
