import data_handlers.president.converter as converter
import data_handlers.parser as parser
import data_handlers.templates as tp
import data_handlers.helpers as hp

### Generator functions
def generate_country_json(preprocessing_data, is_running, is_started , helper=hp.helper):
    '''
    Input:
        preprocessing_data - cec president data after preprocessing county
        helper             - helper file which helps you map some data in raw cec
    Output:
        country_json - result
    '''
    ### Categorize the original data, and save it in country template
    country_json = tp.CountryTemplate(
        updatedAt  = preprocessing_data['updateAt'],
        is_running = is_running,
        is_started = is_started
    ).to_json()

    ### Generate summary
    preprocessing_districts = preprocessing_data['districts']
    summary_data = preprocessing_districts[hp.COUNTRY_CODE][0]

    raw_candidates = summary_data.get('candTksInfo', hp.DEFAULT_LIST)
    candidates = converter.convert_candidate_president(raw_candidates)

    country_json['summary'] = tp.DistrictTemplate(
        region    = hp.mapping_city[hp.COUNTRY_CODE],
        profRate   = summary_data.get('profRate', hp.DEFAULT_FLOAT),
        candidates  = candidates
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
        candidates = converter.convert_candidate_president(raw_candidate)

        district_tmp['candidates'] = candidates
        country_json['districts'].append(district_tmp)
    return country_json


def generate_county_json(preprocessing_data, is_running, is_started, helper=hp.helper):
    '''
        Generate county json for assigned county_code
        Input:
            preprocessing_data  - cec data after preprocessing county`
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
        if county_code in hp.NO_PROCESSING_CODE or raw_county_data==None:
            continue
        preprocessing_town = parser.parse_town(county_code, raw_county_data) # This operation may can be reused

        ### Transform the data
        county_json = tp.CountyTemplate(
            updatedAt  = updateAt,
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
            district_tmp['candidates'] = converter.convert_candidate_president(raw_candidates)

            county_json['districts'].append(district_tmp)
        result[f'{county_code}.json'] = county_json
    return result


def generate_town_json(town_data, updateAt, is_running, is_started, helper=hp.helper):
    '''
    Warning:
        Village data only exist in final.json, don't call this function when the data is running.json

    Description:
        Given the data of the town, generate the json data for the village.
        There are no direct village code in raw data, you should map the tboxNo to it.
        Besides, the village data only exist in final.json

    Input:
        town_data - The data after parse_president_town(county_code, county_data)
        helper    - helper dict

    Output:
        result - The dict content {str: filename, dict: json}.
        [Example] You will get the result like this:
        {
            '09007010', 09007010.json <= this is the data you need to generate
            '09007020', 09007020.json <= this is the data you need to generate
            ...
        }

        errors - The error list which record all the problematic tboxNo
    '''
    if is_running == True:
        print('generate_town_json can only be called when the data is final.json')
        return None

    result = {}
    errors = []
    county_code = town_data.get('county_code', None)
    if county_code == None:
        print('invalid town data without county_code provided')

    for town_code, tbox_data in town_data['towns'].items():
        if town_code == hp.DEFAULT_VILLCODE:
            continue
        filename = f'{county_code}{town_code}.json'
        vill_json = tp.TownTemplate(
            updatedAt = updateAt,
            is_running = is_running,
            is_started = is_started,
        ).to_json()
        
        ### 這邊進來的是投票所的資料，要將其mapping到對應的村里
        vill_calculator = {}
        for data in tbox_data:
            tboxNo    = data.get('tboxNo', hp.DEFAULT_INT)
            voterTurnout   = data.get('voterTurnout', hp.DEFAULT_INT)
            eligibleVoters = data.get('eligibleVoters', hp.DEFAULT_INT)
            if tboxNo == 0:
                continue
            ### 比對村里資訊，我們會使用county_code,town_code,tboxNo調閱該對應投票所所擁有的村里再進行計算
            # df = hp.mapping_tbox
            # filter_df = df[(df['countyCode']==str(county_code)) & (df['townCode']==str(town_code)) & (df['tboxNo']==str(tboxNo))]
            # vill_list = list(filter_df['village'])
            # for vill_name in vill_list:
            #     vill_code = hp.mapping_vill_code.get(county_code+town_code, {}).get(vill_name, None)
            #     if vill_code == None:
            #         message = f'tboxNo: {tboxNo} has no mapping data'
            #         error = tp.ErrorTemplate(
            #             county = county_code, 
            #             town   = town_code, 
            #             reason = message
            #         ).to_json
            #         errors.append(error)
            #     all_code = f'{county_code}{town_code}{vill_code}'
            #     vill_calc = vill_calculator.get(all_code, None)
            #     if vill_calc == None:
            #         region = hp.mapping_town.get(county_code+town_code, 'Unknown') + hp.mapping_vill.get(all_code, 'Unknown')
            #         vill_calc_json = tp.VillCalcTemplate(
            #             region       = region,
            #             county       = county_code,
            #             town         = town_code,
            #             vill         = vill_code,
            #             voterTurnout   = voterTurnout,
            #             eligibleVoters = eligibleVoters
            #         ).to_json()
            #         raw_candidates = data.get('candTksInfo', [])
            #         vill_calc_json['candidates'] = converter.convert_candidate_president(raw_candidates)
            #         for cand in vill_calc_json['candidates']:
            #             cand['candVictor'] = ' ' ### Haven't finished calculation yet, so no winner for candidates
            #         vill_calculator[all_code] = vill_calc_json
            #     else:
            #         vill_calc['voterTurnout']   += voterTurnout
            #         vill_calc['eligibleVoters'] += eligibleVoters
            #         candidates = converter.convert_candidate_president(data.get('candTksInfo', []))
            #         for idx, cand in enumerate(vill_calc['candidates']):
            #             cand['tks'] += candidates[idx]['tks']
            vill_name = hp.mapping_tboxno_vill.get(county_code+town_code, {}).get(str(tboxNo), None)
            vill_code = hp.mapping_vill_code.get(county_code+town_code, {}).get(vill_name, None)
            if vill_code == None:
                message = f'tboxNo: {tboxNo} has no mapping data'
                error = tp.ErrorTemplate(
                    county = county_code, 
                    town   = town_code, 
                    reason = message
                ).to_json
                errors.append(error)
            
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
                vill_calc_json['candidates'] = converter.convert_candidate_president(raw_candidates)
                for cand in vill_calc_json['candidates']:
                    cand['candVictor'] = ' ' ### Haven't finished calculation yet, so no winner for candidates
                vill_calculator[all_code] = vill_calc_json
            else:
                vill_calc['voterTurnout']   += voterTurnout
                vill_calc['eligibleVoters'] += eligibleVoters
                
                candidates = converter.convert_candidate_president(data.get('candTksInfo', []))
                for idx, cand in enumerate(vill_calc['candidates']):
                    cand['tks'] += candidates[idx]['tks']
        for all_code, vill_calc in vill_calculator.items():
            region, county, town, vill = vill_calc['region'], vill_calc['county'], vill_calc['town'], vill_calc['vill']
            total_voterTurnout   = vill_calc.get('voterTurnout', hp.DEFAULT_INT)
            total_eligibleVoters = vill_calc.get('eligibleVoters', hp.DEFAULT_INT)
            profRate = round((total_voterTurnout/total_eligibleVoters)*100, hp.ROUND_DECIMAL)
            
            total_tks, winner_idx = 0,0
            candidates = vill_calc['candidates']
            for idx, cand in enumerate(candidates):
                tks = cand.get('tks', hp.DEFAULT_INT)
                total_tks += tks
                if tks>candidates[winner_idx]['tks']:
                    winner_idx = idx
            for idx, cand in enumerate(candidates):
                cand['tksRate'] = round((cand['tks']/total_tks)*100, hp.ROUND_DECIMAL)
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
    return result, errors