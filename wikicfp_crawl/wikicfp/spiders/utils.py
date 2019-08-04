import scrapy
from typing import List
from flair.data import Sentence
from flair.models import SequenceTagger
from segtok.segmenter import split_single

class Conference(scrapy.Item):

    title = scrapy.Field()
    link = scrapy.Field()
    timetable = scrapy.Field()
    categories = scrapy.Field()
    persons = scrapy.Field()


def conference_to_csv(conference: 'Conference', filepath: str):
    with open(filepath, 'a+') as conference_csv:
        for value in conference.values():
            conference_csv.write('{}\t'.format(value))
        conference_csv.write('\n')


class NER:

    ner_engine = SequenceTagger.load('ner')

    def get_persons(text_blocks: List[List]):
        entities = []
        for text_block in text_blocks:
            for line in text_block:
                sentences: List[str] = list(filter(lambda sent: sent, split_single(line)))
                sentences: List[Sentence] = [Sentence(sent) for sent in sentences]
                for sentence in sentences:
                    NER.ner_engine.predict(sentence)
                    for entity in sentence.get_spans('ner'):
                        if 'PER' in entity.tag:
                            entities.append(entity.text)
        return entities
