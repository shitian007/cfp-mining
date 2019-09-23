from pathlib import Path

# Scrapy custom settings
DOWNLOAD_DELAY = 0.5
DOWNLOAD_TIMEOUT = 30

# Type of NER: Flair / None
NER_TYPE = None

# Set arbitrary browser agent in header since certain sites block against crawlers
REQUEST_HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'}

# Save filepath for csv to scraped conferences
curr_dir = Path(__file__).parent.resolve()
data_dir = Path.joinpath(curr_dir.parent, 'data/')
DB_FILEPATH = Path.joinpath(data_dir, 'conferences_latest_23_09.db')