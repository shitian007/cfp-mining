from .utils import Conference
from .extractors import BlockExtractor, LineInfoExtractor


def extract_line_information(cnx,
                             extract_type, indent_diff, linenum_diff,
                             start_index, end_index):
    cur = cnx.cursor()
    block_extractor = BlockExtractor(cur, extract_type)
    lineinfo_extractor = LineInfoExtractor(cur, extract_type)
    conf_ids = cur.execute(
        "SELECT id FROM WikicfpConferences WHERE accessible LIKE '%Accessible%' ORDER BY id").fetchall()[start_index:end_index]
    for conf_id in conf_ids:
        conf_id = conf_id[0]
        conf_tuple = cur.execute(
            "SELECT * FROM WikicfpConferences WHERE id=?", (conf_id,)).fetchone()
        relevant_blocks = block_extractor.get_relevant_blocks(conf_id, indent_diff, linenum_diff)
        conference: 'Conference' = Conference(conf_tuple, relevant_blocks)
        lineinfo_extractor.process_conference(conference)
        cnx.commit()

    cur.close()
