import re
from pathlib import Path
from typing import List
from flair.data import Sentence
from flair.models import SequenceTagger
from segtok.segmenter import split_single
from .utils import NER, Conference, conference_to_csv

class ConfParser:

    @staticmethod
    def parse_conf(response):
        """
        Parses only for conference pages, omits for allcfp pages
        """

        if 'allcfp' in response.url:
            return

        # table index varies since certain pages might not contain links
        table_index = {
            "TITLE": 1,
            "LINK": 2,
            "TIMETABLE": 4,
            "MAIN": 7
            }

        # Get table containing CFP info
        table_main = response.xpath('//div[contains(@class, "contsec")]/center/table')
        table_rows = table_main.xpath('tr')

        # Get title
        conference_title: str = table_rows[table_index["TITLE"]].xpath('td/h2//span[contains(@property, "v:description")]/text()').get().strip()

        # Certain conference pages might not contain link considering it is not mandatory
        conference_link: str = table_rows[table_index["LINK"]].xpath('td/a/@href').get()
        if not conference_link:
            table_index["TIMETABLE"] = table_index["TIMETABLE"] - 1
            table_index["MAIN"] = table_index["MAIN"] - 1

        # Inner table containing timetable and category info are highly nested
        inner_table: 'Selector' = table_rows[table_index["TIMETABLE"]].xpath('.//tr//table')[0]
        timetable_info, category_info = ConfParser.get_innertable_info(inner_table) # timetable_info: Dict, category_info: List

        # Main block of information
        cfp_main_block = table_rows[table_index["MAIN"]]
        persons = ConfParser.process_cfp_main(cfp_main_block)

        conference: Conference = Conference(
            title = conference_title,
            link = conference_link,
            timetable = timetable_info,
            categories = category_info,
            persons = persons
            )

        # curr_dir = Path(__file__).parent.resolve()
        # csv_path = Path.joinpath(curr_dir.parent.parent, 'conferences.csv')
        # conference_to_csv(conference, csv_path)
        # print("=========================")
        # print("Saving to: {}".format(csv_path))
        # print("=========================")

        return conference


    @staticmethod
    def get_innertable_info(inner_table: 'Selector'):
        """
        Gets information of inner table containing timetable and category information
        Arguments:
            inner_table: root `tr` with 2 nested `tr`s of timetable and category info
        """
        timetable, category_info = tuple(inner_table.xpath('./tr'))
        # Get all info on category_info
        category_info = category_info.xpath('.//a[contains(@href, "call")]/text()').getall()
        # Get all info from timetable
        time_locale_fields = ["When", "Where"]
        deadline_fields = ["Submission Deadline", "Notification Due", "Final Version Due", "Abstract Registration Due"]
        timetable_info = {}
        timetable_info_rows = timetable.xpath('.//tr')
        for info_row in timetable_info_rows:
            field_key = info_row.xpath('./th/text()').get().strip()
            if field_key in time_locale_fields:
                field_value = info_row.xpath('td/text()').get().strip()
            elif field_key in deadline_fields:
                field_value_parent = info_row.xpath('./td/span') # TBD field is not nested
                if field_value_parent:
                    field_value = field_value_parent.xpath('./span[@property="v:startDate"]/text()').get().strip()
                else:
                    field_value = info_row.xpath('./td/text()').get().strip()
            else:
                raise("Undefined inner table property: {}".format(field_key))
            timetable_info[field_key] = field_value

        return timetable_info, category_info


    @staticmethod
    def process_cfp_main(main_block: 'Selector'):

        text_lines = main_block.xpath('.//div/text()').getall()

        # Remove `\r` due to <br> nodes, use extra line breaks as block separator
        text_lines = [text_line.rstrip() for text_line in text_lines]
        text_blocks: List[List] = []
        block: List = []
        for text_line in text_lines:
            if not text_line:
                if block:
                    text_blocks.append(block)
                block = []
            else:
                block.append(text_line)
        text_blocks.append(block)

        persons = []
        # persons = NER.get_persons(text_blocks)
        return persons
