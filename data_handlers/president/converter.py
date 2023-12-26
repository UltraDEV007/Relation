import data_handlers.templates as tp
import data_handlers.helpers as hp

'''
    Converters are used to convert some raw data into object template
'''

def convert_candidate_president(raw_candidates):
    '''
    Description:
        Convert the raw candidates data into CandidateTemplate
    '''
    result = []
    for cand in raw_candidates:
        candidate_tmp = tp.CandidateTemplate().to_json()
        candNo = cand.get('candNo', 0)
        candidate_tmp['candNo']     = candNo
        candidate_tmp['name']       = hp.mapping_president.get(str(candNo), hp.UNKNOWN_CANDIDATE).get('name', None)
        candidate_tmp['party']      = hp.mapping_president.get(str(candNo), hp.UNKNOWN_CANDIDATE).get('party', None)
        candidate_tmp['tks']        = cand.get('tks', hp.DEFAULT_INT)
        candidate_tmp['tksRate']    = round(cand.get('tksRate', hp.DEFAULT_FLOAT), hp.ROUND_DECIMAL)
        candidate_tmp['candVictor'] = cand.get('candVictor', '')
        result.append(candidate_tmp)
    return result