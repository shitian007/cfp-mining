from pathlib import Path

# Scrapy download delay
DOWNLOAD_DELAY = 0.5

# Type of NER: Flair / None
NER_TYPE = None

# Save filepath for csv to scraped conferences
curr_dir = Path(__file__).parent.resolve()
CSV_FILEPATH = Path.joinpath(curr_dir.parent.parent, 'conferences_temp.csv')
