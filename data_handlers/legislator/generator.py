import copy
import data_handlers.helpers as hp
import data_handlers.templates as tp
import data_handlers.parser as parser
import data_handlers.legislator.converter as converter

'''
    Generate constituency(區域立委)
'''
def generate_constituency_json(preprocessing_data, is_running, is_started , helper=hp.helper):
    '''
    Input:
        preprocessing_data - cec constituency data(L1) after preprocessing area
        helper             - helper file which helps you map the name in raw cec
    Output:
        country_json - result
    '''
    if is_running == True:
        print("Don't call generate_constituency_json when the data is running.json")
        return None
    
    result = {}
    
    ### 在每一個行政區(district)下有很多投票所，將這些資料進行整理計算並存到result
    for county_area_code, tbox_data in preprocessing_data['districts'].items():
        constituency_json = tp.ConstituencyTemplate(
            is_running = is_running,
            is_started = is_started
        ).to_json()
        constituency_json['updateAt'] = preprocessing_data['updateAt']
        
        ### 當為全省(台灣省,福建省)資料和無地區資料時不處理
        county_code = county_area_code[:hp.COUNTY_CODE_LENGTH]
        area_code   = county_area_code[hp.COUNTY_CODE_LENGTH:]  
        if county_code in hp.NO_PROCESSING_CODE or area_code == hp.DEFAULT_AREACODE:
            continue
        
        ### 票數計算
        for data in tbox_data:
            tboxNo    = data.get('tboxNo', hp.DEFAULT_INT)
            town_code = data.get('deptCode', hp.DEFAULT_TOWNCODE)
            area_code = data.get('areaCode', hp.DEFAULT_AREACODE)
            profRate  = data.get('profRate', hp.DEFAULT_FLOAT)
            if tboxNo == hp.DEFAULT_INT or town_code == hp.DEFAULT_TOWNCODE or area_code == hp.DEFAULT_AREACODE:
                continue
                
            vill_name = hp.mapping_tboxno_vill.get(county_code+town_code, {}).get(str(tboxNo), None)
            vill_code = hp.mapping_vill_code.get(county_code+town_code, {}).get(vill_name, None)
            
            #TODO: 產生地區字串(範例: 連江縣 第01選區 南竿鄉介壽村)，須重構
            town_name = hp.mapping_town[f'{county_code}{town_code}']
            city_name = town_name[:3] ## TODO: Should refactor
            region = f'{city_name} 第{area_code}選區 {town_name[3:]}{vill_name}'
            
            district_tmp = tp.ConstituencyDistrictTemplate(
                region = region,          
                area_nickname = hp.mapping_nickname[f'{county_code}{area_code}'],
                county_code = county_code,
                area = area_code,
                town = town_code,
                vill = vill_code,
                type_str = "normal",
                profRate = profRate
            ).to_json()
            raw_candidate = data.get('candTksInfo', [])
            candidates = converter.convert_constituency_candidate(raw_candidate, county_code, area_code)
            district_tmp['candidates'] = candidates
            constituency_json['districts'].append(district_tmp)
        result[f'{county_area_code}.json'] = constituency_json
    return result

def generate_country_json(preprocessing_data, is_running, is_started , election_type, helper=hp.helper):
    '''
    Input:
        preprocessing_data - cec president data after preprocessing county
        is_running         - is_running file?
        is_started         - is_started?
        election_type      - 'mountainIndigenous'/'plainIndigenous'/'party'
        helper             - helper file which helps you map the name in raw cec
    Output:
        country_json - result
    '''
    ### Categorize the original data, and save it in country template
    preprocessing_data = copy.deepcopy(preprocessing_data)
    country_json = tp.CountryTemplate(
        is_running = is_running,
        is_started = is_started
    ).to_json()
    country_json['updateAt'] = preprocessing_data['updateAt']

    ### Generate summary
    preprocessing_districts = preprocessing_data['districts']
    summary_data = preprocessing_districts[hp.COUNTRY_CODE][0]

    raw_candidates = summary_data.get('candTksInfo', hp.DEFAULT_LIST)
    candidates = converter.convert_candidate(raw_candidates, election_type)

    country_json['summary'] = tp.DistrictTemplate(
        region     = hp.mapping_city[hp.COUNTRY_CODE],
        profRate   = summary_data.get('profRate', hp.DEFAULT_FLOAT),
        type_str   = None if election_type=='president' else election_type, ###總統大選以外需要標明type
        candidates = candidates
    ).to_json()
        
    ### Generate districts
    for county_code, values in preprocessing_districts.items():
        if county_code in hp.NO_PROCESSING_CODE:
            continue
        county_str  = hp.mapping_city.get(county_code, None)
        county_data = values[0]
        if county_str == None:
            continue

        district_tmp = tp.DistrictTemplate(
            region   = county_str,
            county_code = county_code
        ).to_json()
        district_tmp['profRate'] = county_data.get(helper['PROFRATE'], hp.DEFAULT_FLOAT)

        raw_candidate = county_data.get('candTksInfo', [])
        candidates = converter.convert_candidate(raw_candidate, election_type)

        district_tmp['candidates'] = candidates
        country_json['districts'].append(district_tmp)
    return country_json

def generate_county_json(preprocessing_data, is_running, is_started, election_type, helper=hp.helper):
    '''
        Generate county json for assigned county_code
        Input:
            preprocessing_data  - cec data after preprocessing county
        Output:
            result - {filename, county_json}
    '''
    ### Invalid parameters checking
    if preprocessing_data==None:
        print('Please specify the data')
        return None
    districts = preprocessing_data.get('districts', None)
    if districts == None:
        print('Please provide the data with districts')
        return None

    ### Initialize some data
    result = {}
    updateAt = preprocessing_data['updateAt']

    for county_code, raw_county_data in districts.items():
        if (county_code in hp.NO_PROCESSING_CODE) or raw_county_data==None:
            continue
        preprocessing_town = parser.parse_town(county_code, raw_county_data)

        ### Transform the data
        county_json = tp.CountyTemplate(
            updateAt   = updateAt,
            is_running = is_running,
            is_started = is_started
        ).to_json()
        for town_code, town_data in preprocessing_town['towns'].items():
            if town_code == hp.DEFAULT_TOWNCODE:
                continue
            county_town_code = f'{county_code}{town_code}'

            district_tmp = tp.DistrictTemplate(
                region = hp.mapping_town.get(county_town_code, ''),
                county_code = county_code,
                town = town_code,
                profRate = town_data[0][helper['PROFRATE']]

            ).to_json()
            raw_candidates = town_data[0].get(helper['CANDIDATES'], [])
            district_tmp['candidates'] = converter.convert_candidate(raw_candidates, election_type)

            county_json['districts'].append(district_tmp)
        result[f'{county_code}.json'] = county_json
    return result

def generate_town_json(town_data, updateAt, is_running, is_started, election_type, helper=hp.helper):
    '''
    Description:
        Given the data of the town, generate the json data for the village.
        There are no direct village code in raw data, you should map the tboxNo to it.
        Besides, the village data only exist in final.json

    Input:
        town_data     - The data after parse_president_town(county_code, county_data)
        election_type - 'mountainIndigenous'/'plainIndigenous'
        helper        - helper dict

    Output:
        result - The dict content {str: filename, dict: json}.
        [Example] You will get the result like this:
        {
            '09007010', 09007010.json <= this is the data you need to generate
            '09007020', 09007020.json <= this is the data you need to generate
            ...
        }
    '''
    result = {}

    county_code = town_data.get('county_code', None)
    if county_code == None or (county_code in hp.NO_PROCESSING_CODE):
        return None
    
    for town_code, tbox_data in town_data['towns'].items():
        if town_code == hp.DEFAULT_VILLCODE:
            continue
        filename = f'{county_code}{town_code}.json'
        vill_json = tp.TownTemplate(
            updateAt = updateAt,
            is_running = is_running,
            is_started = is_started,
        ).to_json()
        
        ### 這邊進來的是投票所的資料，要將其mapping到對應的村里
        vill_calculator = {}
        for data in tbox_data:
            tboxNo    = data.get('tboxNo', hp.DEFAULT_INT)
            voterTurnout   = data.get('voterTurnout', hp.DEFAULT_INT)
            eligibleVoters = data.get('eligibleVoters', hp.DEFAULT_INT)
            if tboxNo == hp.DEFAULT_INT:
                continue
            
            vill_name = hp.mapping_tboxno_vill.get(county_code+town_code, {}).get(str(tboxNo), None)
            vill_code = hp.mapping_vill_code.get(county_code+town_code, {}).get(vill_name, None)
            
            all_code = f'{county_code}{town_code}{vill_code}'
            vill_calc = vill_calculator.get(all_code, None)
            if vill_calc == None:
                region = hp.mapping_town.get(county_code+town_code, 'Unknown') + hp.mapping_vill.get(all_code, 'Unknown')
                vill_calc_json = tp.VillCalcTemplate(
                    region       = region,
                    county       = county_code,
                    town         = town_code,
                    vill         = vill_code,
                    voterTurnout   = voterTurnout,
                    eligibleVoters = eligibleVoters
                ).to_json()
                raw_candidates = data.get('candTksInfo', [])
                vill_calc_json['candidates'] = converter.convert_candidate(raw_candidates, election_type)
                
                ### 在不分區立委(party)當中不會有獲勝者的資料，不需要處理。其他的話由於需要在最後統算時才能得出winner所以要先設為空字串 
                if election_type != 'party':
                    for cand in vill_calc_json['candidates']:
                        cand['candVictor'] = ' '
                vill_calculator[all_code] = vill_calc_json
            else:
                vill_calc['voterTurnout']   += voterTurnout
                vill_calc['eligibleVoters'] += eligibleVoters
                
                candidates = converter.convert_candidate(data.get('candTksInfo', []), election_type)
                for idx, cand in enumerate(vill_calc['candidates']):
                    cand['tks'] += candidates[idx]['tks']
        
        for all_code, vill_calc in vill_calculator.items():
            region, county, town, vill = vill_calc['region'], vill_calc['county'], vill_calc['town'], vill_calc['vill']
            total_voterTurnout   = vill_calc.get('voterTurnout', hp.DEFAULT_INT)
            total_eligibleVoters = vill_calc.get('eligibleVoters', hp.DEFAULT_INT)
            profRate = round((total_voterTurnout/total_eligibleVoters)*100, 2) if total_eligibleVoters!=hp.DEFAULT_INT else hp.DEFAULT_FLOAT
            
            total_tks, winner_idx = 0,0
            candidates = vill_calc['candidates']
            for idx, cand in enumerate(candidates):
                tks = cand.get('tks', hp.DEFAULT_INT)
                total_tks += tks
                if tks>candidates[winner_idx]['tks']:
                    winner_idx = idx
            for idx, cand in enumerate(candidates):
                cand['tksRate'] = round((cand['tks']/total_tks)*100, hp.ROUND_DECIMAL) if total_tks!=hp.DEFAULT_INT else hp.DEFAULT_FLOAT
            if election_type != 'party':
                candidates[winner_idx]['candVictor'] = '*' 
            
            ### Store the calculated result into DistrictTemplate
            district_json = tp.DistrictTemplate(
                region      = region,
                county_code = county,
                town        = town,
                vill        = vill,
                profRate    = profRate
            ).to_json()
            
            district_json['candidates'] = candidates
            vill_json['districts'].append(district_json)
        result[filename] = vill_json
    return result