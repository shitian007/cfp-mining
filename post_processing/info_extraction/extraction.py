from .utils import Conference, consolidate_line_nums
from .extractors import BlockExtractor, LineInfoExtractor


def extract_line_information(cnx, extract_type, ner_extract_type,
                             indent_diff, linenum_diff, conf_ids):
    cur = cnx.cursor()
    block_extractor = BlockExtractor(cur, extract_type)
    lineinfo_extractor = LineInfoExtractor(cur, extract_type, ner_extract_type)
    for conf_id in conf_ids:
        accessibility = cur.execute("SELECT accessible FROM WikicfpConferences WHERE id=?", (conf_id,)).fetchone()
        accessibility = accessibility[0] if accessibility else ""
        if 'Accessible' in accessibility:
            print("=========================== Info extraction ({}) for Conference {} =================================".format(ner_extract_type, conf_id))
            conf_tuple = cur.execute(
                "SELECT * FROM WikicfpConferences WHERE id=?", (conf_id,)).fetchone()
            relevant_blocks = block_extractor.get_relevant_blocks(
                conf_id, indent_diff, linenum_diff)
            relevant_blocks = consolidate_line_nums(relevant_blocks)
            conference: 'Conference' = Conference(conf_tuple, relevant_blocks)
            lineinfo_extractor.process_conference(conference)
            cnx.commit()
        else:
            print("=========================== Inaccessible Conference {} =================================".format(conf_id))

    cur.close()
