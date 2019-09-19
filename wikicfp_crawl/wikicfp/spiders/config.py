from pathlib import Path

# Scrapy custom settings
DOWNLOAD_DELAY = 0.5
DOWNLOAD_TIMEOUT = 30

# Type of NER: Flair / None
NER_TYPE = None

# Save filepath for csv to scraped conferences
curr_dir = Path(__file__).parent.resolve()
CSV_FILEPATH = Path.joinpath(curr_dir.parent.parent, 'conferences_all_12_09_19.csv')
CSV_HEADERS = ['title', 'link', 'timetable', 'categories', 'aux_links', 'persons', 'nil']
