import data_handlers.templates as tp
import data_handlers.helpers as hp

def convert_constituency_candidate(raw_candidates, county_code:str, area_code:str):
    '''
    Description:
        Convert constituency candidate into CandidateTemplate. Because the mapping hierarchy of constituency
        is quite different from others, don't call convert_candidate to do it.
    Input:
        raw_candidates: candidates data
        county_code: For example, '65000'/'10014'...
        area_code: For example: '01'/'02'...
    '''
    result = []
    area_code = area_code.zfill(2)
    area_candidates = hp.mapping_constituency_cand.get(county_code, {}).get(area_code, None)
    if area_candidates == None:
        return None
    for cand in raw_candidates:
        candidate_tmp = tp.CandidateTemplate().to_json()
        candNo = cand.get('candNo', 0)
        candidate_tmp['candNo']     = candNo
        candidate_tmp['name']       = area_candidates.get(str(candNo), {}).get('person', hp.UNKNOWN_CANDIDATE).get('name', None)
        candidate_tmp['party']      = area_candidates.get(str(candNo), hp.UNKNOWN_CANDIDATE).get('party', None)
        candidate_tmp['tks']        = cand.get('tks', hp.DEFAULT_INT)
        candidate_tmp['tksRate']    = round(cand.get('tksRate', hp.DEFAULT_FLOAT), hp.ROUND_DECIMAL)
        candidate_tmp['candVictor'] = cand.get('candVictor', ' ')
        result.append(candidate_tmp)
    return result

def convert_candidate(raw_candidates, election_type):
    '''
    Description:
        Convert the raw candidates data into CandidateTemplate, mapping file will depend on election_type
    Input:
        raw_candaidates: candidates data
        election_type: 'mountainIndigenous'/'plainIndigenous'/'party'
    Warning:
        The raw_candidates field in election_type=='party' is different from others
    '''
    result = []
    
    ### Choose the correct mapping file
    mapping_relationship = {
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
            
            candVictor = cand.get('candVictor', ' ')
            if len(candVictor) == 0:
                candVictor = ' '
            candidate_tmp['candVictor'] = candVictor
            result.append(candidate_tmp)
    else:
        for cand in raw_candidates:
            candidate_tmp = tp.PartyCandidateTemplate().to_json()
            patyNo = cand.get('patyNo', hp.DEFAULT_INT)
            candidate_tmp['candNo']  = patyNo
            candidate_tmp['party']   = mapping_json.get(str(patyNo), hp.UNKNOWN_PARTY).get('name', None)
            candidate_tmp['seats']   = mapping_json.get(str(patyNo), hp.UNKNOWN_PARTY).get('seat', None)
            candidate_tmp['tksRate'] = round(cand.get('tksRate1', hp.DEFAULT_FLOAT), hp.ROUND_DECIMAL) ### Don't use tksRate2
            candidate_tmp['tks']     = cand.get('tks', hp.DEFAULT_INT)
            result.append(candidate_tmp)
    return result