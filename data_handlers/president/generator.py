import os
import json
import copy

import templates as tp
import helpers as hp
from helpers import helpers

### Load mapping_city.json
root = os.path.join('..', '..', 'mapping', '2024')
path = os.path.join(root, 'mapping_city.json')
with open(path, mode='r', encoding='utf-8') as f:
    mapping_city = json.load(f)
    print('open mapping_city.json successed')
    
path = os.path.join(root, 'mapping_prv_city.json')
with open(path, mode='r', encoding='utf-8') as f:
    mapping_prv_city = json.load(f)
    print('open mapping_prv_city.json successed')
    
path = os.path.join(root, 'mapping_prv_city_vill.json')
with open(path, mode='r', encoding='utf-8') as f:
    mapping_prv_city_vill = json.load(f)
    print('open mapping_prv_city_vill.json successed')

### Generator functions
def generate_country_json(preprocessing_data, is_started: bool, is_running: bool, helper=helpers['2024']):
    '''
    Input:
        preprocessing_data - cec president data after preprocessing
        helper             - helper file which helps you map the name in raw cec 
    Output:
        country_json - result
    '''
    ### Data checking
    if preprocessing_data == None:
        print("You should provide preprocessing_data to generate_country_json")
        return None
    preprocessing_data = copy.deepcopy(preprocessing_data)

    ### Categorize the original data, and save it in country template
    president_mapping  = helper['CAND_PRESIDENT_MAPPING']
    
    country_json = tp.CountryTemplate().to_json()
    country_json['updateAt'] = preprocessing_data['updateAt']
    country_json['is_started'] = is_started
    country_json['is_running'] = is_running

    ### Generate summary
    COUNTRY_CODE = '00000'
    preprocessing_districts = preprocessing_data['districts']
    summary_data = preprocessing_districts[COUNTRY_CODE][0]
    summary_candidates = summary_data.get('candTksInfo', hp.DEFAULT_LIST)
    candidates = [ tp.CandidateTemplate().to_json() for _ in range(len(summary_candidates)) ]
    
    for idx, candInfo in enumerate(candidates):
        raw_candInfo = summary_candidates[idx]
        # Candidate information
        candNo = raw_candInfo.get('candNo', hp.DEFAULT_INT)
        candInfo['candNo'] = candNo
        candInfo['name']   = president_mapping.get(candNo, hp.UNKNOWN_CANDIDATE).get('name')
        candInfo['party']  = president_mapping.get(candNo, hp.UNKNOWN_CANDIDATE).get('party')
        candInfo['candVictor'] = raw_candInfo.get('candVictor', '')
        # Candidate tickers calculation 
        candInfo['tksRate'] = round(raw_candInfo.get('tksRate', hp.DEFAULT_INT), 2)
        candInfo['tks'] = raw_candInfo.get('tks', hp.DEFAULT_INT)
    
    country_json['summary'] = tp.DistrictTemplate(
        county_str  = mapping_city[COUNTRY_CODE],
        profRate    = summary_data.get('profRate', hp.DEFAULT_FLOAT),
        candidates  = candidates
    ).to_json()
    try:
        del preprocessing_districts[COUNTRY_CODE]
    except KeyError as e:
        print(f"Delete COUNTRY_CODE data failed at {country_json['updateAt']}")
    
    ### Generate districts
    for county_code, values in preprocessing_districts.items():
        county_str  = mapping_city.get(county_code, None)
        county_data = values[0] 
        if county_str == None:
            continue
        
        district_tmp = tp.DistrictTemplate(
            county_str  = county_str,
            county_code = county_code
        ).to_json()
        district_tmp['profRate'] = county_data.get(helper['PROFRATE'], hp.DEFAULT_FLOAT)
        
        raw_candidate = county_data.get('candTksInfo', [])
        candidates = [ tp.CandidateTemplate().to_json() for _ in range(len(raw_candidate)) ]
        for idx, candInfo in enumerate(candidates):
            candNo             = raw_candidate[idx].get('candNo', hp.DEFAULT_INT)
            candInfo['candNo'] = candNo
            candInfo['name']   = president_mapping.get(candNo, hp.UNKNOWN_CANDIDATE).get('name')
            candInfo['party']  = president_mapping.get(candNo, hp.UNKNOWN_CANDIDATE).get('party')
            candInfo['tksRate']    = round(raw_candidate[idx].get('tksRate', hp.DEFAULT_FLOAT), 2)
            candInfo['candVictor'] = raw_candidate[idx].get('candVictor', ' ')
            candInfo['tks']        = raw_candidate[idx].get('tks', hp.DEFAULT_INT)
        district_tmp['candidates'] = candidates
        country_json['districts'].append(district_tmp)
    return country_json

def generate_county_json(preprocessing_data, county_code: str, is_started: bool, is_running: bool, helper=helpers['2024']):
    '''
        Generate county json for assigned county_code
        Input:
            preprocessing_data   - cec data after preprocessing
            county_code          - `${prvCode}${cityCode}`
        Output:
            county_json - json result
    '''
    ### Invalid parameters checking
    if preprocessing_data==None or county_code==None:
        print('Please specify the data and county_code')
        return None
    preprocessing_data = copy.deepcopy(preprocessing_data)
    
    ### Initialize some data
    president_mapping = helper['CAND_PRESIDENT_MAPPING']
    county_json = tp.CountyTemplate().to_json()
    county_json['updateAt'] = preprocessing_data['updateAt']
    county_json['is_starting'] = is_started
    county_json['is_running']  = is_running
    
    ### Fetch the data
    districts = preprocessing_data.get('districts', None)
    if districts == None:
        print('Please provide the correct preprocessing data')
        return None
    raw_county_data = districts.get(county_code, None)
    if raw_county_data == None:
        print(f'Could not find the corresponding data for {county_code}')
        return None
    
    ### Transform the data
    for row_town_data in raw_county_data:
        town_code = row_town_data[helper['TOWN']]
        vill_code = f'{county_code}{town_code}'
        
        district_tmp = tp.DistrictTemplate().to_json()
        district_tmp['range']    = mapping_prv_city_vill.get(vill_code, '')
        district_tmp['county']   = county_code
        district_tmp['town']     = town_code
        district_tmp['profRate'] = row_town_data[helper['PROFRATE']]
        
        row_candidates = row_town_data.get(helper['CANDIDATES'], [])
        for row_candidate in row_candidates:
            candidate_tmp = tp.CandidateTemplate().to_json()
            candNo = row_candidate.get('candNo', 0)
            candidate_tmp['candNo']     = candNo
            candidate_tmp['name']       = president_mapping.get(candNo, hp.UNKNOWN_CANDIDATE).get('name', None)
            candidate_tmp['party']      = president_mapping.get(candNo, hp.UNKNOWN_CANDIDATE).get('party', None)
            candidate_tmp['tks']        = row_candidate.get('tks', 0)
            candidate_tmp['tksRate']    = row_candidate.get('tksRate', 0.0)
            candidate_tmp['candVictor'] = row_candidate.get('candVictor', ' ')
            district_tmp['candidates'].append(candidate_tmp)
        county_json['districts'].append(district_tmp)
    return county_json