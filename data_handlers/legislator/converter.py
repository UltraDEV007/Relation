import data_handlers.templates as tp
import data_handlers.helpers as hp

def convert_candidate(raw_candidates, election_type, helper):
    '''
    Description:
        Convert the raw candidates data into CandidateTemplate, mapping file will depend on election_type
    Input:
        raw_candaidates: candidates data
        election_type: 'constituency'/'mountainIndigenous'/'plainIndigenous'/'party'
    Warning:
        The raw_candidates field in election_type=='party' is different from others
    '''
    result = []
    
    ### Choose the correct mapping file
    mapping_relationship = {
        'constituency': hp.mapping_constituency_cand,
        'plainIndigenous': hp.mapping_plain_cand,
        'mountainIndigenous': hp.mapping_mountain_cand,
        'party': hp.mapping_party_seat,
    }
    mapping_json = mapping_relationship.get(election_type, None)
    if mapping_json == None:
        print('convert_candidate receive a invalid election_type {election_type}')
        return None
    
    if election_type != 'party':
        for cand in raw_candidates:
            candidate_tmp = tp.CandidateTemplate().to_json()
            candNo = cand.get('candNo', hp.DEFAULT_INT)
            candidate_tmp['candNo']     = candNo
            candidate_tmp['name']       = mapping_json.get(str(candNo), hp.UNKNOWN_CANDIDATE).get('name', None)
            candidate_tmp['party']      = mapping_json.get(str(candNo), hp.UNKNOWN_CANDIDATE).get('party', None)
            candidate_tmp['tks']        = cand.get('tks', hp.DEFAULT_INT)
            candidate_tmp['tksRate']    = round(cand.get('tksRate', hp.DEFAULT_FLOAT), 2)
            candidate_tmp['candVictor'] = cand.get('candVictor', ' ')
            result.append(candidate_tmp)
    else:
        for cand in raw_candidates:
            candidate_tmp = tp.PartyCandidateTemplate().to_json()
            patyNo = cand.get('patyNo', hp.DEFAULT_INT)
            candidate_tmp['candNo']  = patyNo
            candidate_tmp['party']   = mapping_json.get(str(patyNo), hp.UNKNOWN_PARTY).get('name', None)
            candidate_tmp['seats']   = mapping_json.get(str(patyNo), hp.UNKNOWN_PARTY).get('seat', None)
            candidate_tmp['tksRate'] = round(cand.get('tksRate1', hp.DEFAULT_FLOAT), hp.ROUNR_DECIMAL) ### Don't use tksRate2
            candidate_tmp['tks']     = cand.get('tks', hp.DEFAULT_INT)
            result.append(candidate_tmp)
    return result