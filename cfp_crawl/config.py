from pathlib import Path

# Set arbitrary browser agent in header since certain sites block against crawlers
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'}

# Save filepath for csv to scraped conferences
file_name = 'all_28_nov'
# file_name = 'test'
curr_dir = Path(__file__).parent.resolve()

CRAWL_FILEPATH = Path.joinpath(curr_dir.parent, 'crawls/{}/'.format(file_name))
DB_FILEPATH = Path.joinpath(CRAWL_FILEPATH, "{}.db".format(file_name))
LOG_FILEPATH = Path.joinpath(CRAWL_FILEPATH, '{}.log'.format(file_name))

CRAWL_FILEPATH.mkdir(parents=True, exist_ok=True)

# Scrapy custom settings
crawl_settings = {
    'LOG_LEVEL': 'INFO',
    'DOWNLOAD_DELAY': 0.5,
    'DOWNLOAD_TIMEOUT': 30,
    # 'LOG_FILE': LOG_FILEPATH,
    'JOBDIR': CRAWL_FILEPATH,
    'CLOSESPIDER_TIMEOUT': 600
}
