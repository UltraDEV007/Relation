import copy
import data_handlers.helpers as hp
import data_handlers.templates as tp
import data_handlers.parser as parser
import data_handlers.legislator.converter as converter

'''
    Generate constituency(區域立委)
'''
def generate_constituency_county_json(preprocessing_data, is_running, is_started, helper=hp.helper):
    '''
    Input:
        preprocessing_data - cec constituency data(L1) after preprocessing county
        helper             - helper file which helps you map the name in raw cec
    Output:
        result - {f'{county_code}.json': constituency_json}
    '''
    result = {}
    updatedAt = preprocessing_data.get('updateAt','')
    for county_code, county_data in preprocessing_data['districts'].items(): 
        if county_code in hp.NO_PROCESSING_CODE:
            continue
        ### 當county_data只有一個時，表示只有第01選區
        only_one_area = True if len(county_data)==1 else False
        constituency_json = tp.ConstituencyTemplate(
            updatedAt = updatedAt,
            is_running = is_running,
            is_started = is_started,
        ).to_json()

        ### 存入districts資料
        for area_data in county_data:
            area_code = area_data.get('areaCode', hp.DEFAULT_AREACODE)
            if only_one_area:
                area_code = '01'
            else:
                if area_code == hp.DEFAULT_AREACODE:
                    continue
            area_nickname = hp.mapping_nickname.get(f'{county_code}{area_code}', '')
            city_name = hp.mapping_city[county_code]
            region = f'{city_name} 第{area_code}選區'
            profRate = area_data.get('profRate', hp.DEFAULT_FLOAT)
            raw_candidates = area_data.get('candTksInfo', None)
            district_tmp = tp.ConstituencyDistrictTemplate(
                region = region,          
                area_nickname = area_nickname,
                county_code = county_code,
                area = area_code,
                town = None,
                vill = None,
                type_str = "normal",
                profRate = profRate
            ).to_json()
            district_tmp['candidates'] = converter.convert_constituency_candidate(raw_candidates, county_code, area_code)
            
            constituency_json['districts'].append(district_tmp)
        result[f'{county_code}.json'] = constituency_json
    return result

def generate_constituency_town_json(preprocessing_data, is_running, is_started , helper=hp.helper):
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
    preprocessing_data = copy.deepcopy(preprocessing_data)
    updatedAt = preprocessing_data.get('updateAt','')

    only_one_area = ['09007', '09020', '10002', '10014', '10015', '10016', '10017', '10018', '10020']

    ### 在每一個行政區(district)下有很多投票所，將這些資料進行整理計算並存到result
    for county_area_code, tbox_data in preprocessing_data['districts'].items():
        constituency_json = tp.ConstituencyTemplate(
            updatedAt  = updatedAt,
            is_running = is_running,
            is_started = is_started
        ).to_json()
        constituency_json['updateAt'] = preprocessing_data['updateAt']
        
        ### 當為全省(台灣省,福建省)資料和無地區資料時不處理
        county_code = county_area_code[:hp.COUNTY_CODE_LENGTH]
        area_code   = county_area_code[hp.COUNTY_CODE_LENGTH:]  
        if county_code in hp.NO_PROCESSING_CODE:
            continue
        # 處理只有單一選區的縣市問題
        if county_code in only_one_area:
            area_code = '01'
            county_area_code = county_code + area_code
        else:
            if area_code == hp.DEFAULT_AREACODE:
                continue
        
        ### 統計各開票所資料
        vill_calculator = {}
        for data in tbox_data:
            tboxNo         = data.get('tboxNo', hp.DEFAULT_INT)
            town_code      = data.get('deptCode', hp.DEFAULT_TOWNCODE)
            area_code      = area_code #data.get('areaCode', hp.DEFAULT_AREACODE)
            voterTurnout   = data.get('voterTurnout', hp.DEFAULT_INT)
            eligibleVoters = data.get('eligibleVoters', hp.DEFAULT_INT)
            if tboxNo == hp.DEFAULT_INT:
                continue
            
            # 計算各村里的票數總和
            vill_list = hp.mapping_tbox.get(county_code, {}).get(town_code, {}).get(str(tboxNo), [])
            for vill_name in vill_list:
                vill_code = hp.mapping_vill_code.get(county_code+town_code, {}).get(vill_name, None)
                if vill_code == None:
                    continue
                    
                all_code = f'{county_code}{town_code}{vill_code}'
                vill_calc = vill_calculator.get(all_code, None)
                raw_candidates = data.get('candTksInfo', [])
                if vill_calc == None:
                    town_name = hp.mapping_town[f'{county_code}{town_code}']
                    city_name = town_name[:3] ## TODO: Should refactor
                    region = f'{city_name} 第{area_code}選區 {town_name[3:]}{vill_name}'
                    area_nickname = hp.mapping_nickname[f'{county_code}{area_code}']

                    vill_calc_json = tp.ConstituencyCalcTemplate(
                        region         = region,
                        county         = county_code,
                        town           = town_code,
                        area           = area_code,
                        area_nickname = area_nickname,
                        vill           = vill_code,
                        voterTurnout   = voterTurnout,
                        eligibleVoters = eligibleVoters
                    ).to_json()
                    vill_calc_json['candidates'] = converter.convert_constituency_candidate(raw_candidates, county_code, area_code)
                    for cand in vill_calc_json['candidates']:
                        cand['candVictor'] = ' '
                    vill_calculator[all_code] = vill_calc_json
                else:
                    vill_calc['voterTurnout']   += voterTurnout
                    vill_calc['eligibleVoters'] += eligibleVoters
                    candidates = converter.convert_constituency_candidate(raw_candidates, county_code, area_code)
                    for idx, cand in enumerate(vill_calc['candidates']):
                        cand['tks'] += candidates[idx]['tks']
        ### 彙整村里資料並存入ConstituencyDistrictTemplate
        for all_code, vill_calc in vill_calculator.items():
            region, county, town, vill, area = vill_calc['region'], vill_calc['county'], vill_calc['town'], vill_calc['vill'], vill_calc['area']
            area_nickname = vill_calc['area_nickname']
            total_voterTurnout   = vill_calc.get('voterTurnout', hp.DEFAULT_INT)
            total_eligibleVoters = vill_calc.get('eligibleVoters', hp.DEFAULT_INT)
            profRate = round((total_voterTurnout/total_eligibleVoters)*100, hp.ROUND_DECIMAL) if total_eligibleVoters!=hp.DEFAULT_INT else hp.DEFAULT_FLOAT
            
            total_tks, winner_idx = 0,0
            candidates = vill_calc['candidates']
            for idx, cand in enumerate(candidates):
                tks = cand.get('tks', hp.DEFAULT_INT)
                total_tks += tks
                if tks>candidates[winner_idx]['tks']:
                    winner_idx = idx
            for idx, cand in enumerate(candidates):
                cand['tksRate'] = round((cand['tks']/total_tks)*100, hp.ROUND_DECIMAL) if total_tks!=hp.DEFAULT_INT else hp.DEFAULT_FLOAT
            candidates[winner_idx]['candVictor'] = '*' 
            
            ### Store the calculated result into DistrictTemplate
            district_tmp = tp.ConstituencyDistrictTemplate(
                region = region,          
                area_nickname = area_nickname,
                county_code = county,
                area = area,
                town = town,
                vill = vill,
                type_str = "normal",
                profRate = profRate
            ).to_json()
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
        election_type      - 'mountainIndigenous'/'plainIndigenous'/'party'/'president'
        helper             - helper file which helps you map the name in raw cec
    Output:
        country_json - result
    '''
    ### Categorize the original data, and save it in country template
    preprocessing_data = copy.deepcopy(preprocessing_data)
    country_json = tp.CountryTemplate(
        updatedAt  = preprocessing_data['updateAt'],
        is_running = is_running,
        is_started = is_started,
    ).to_json()

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
            updatedAt   = updateAt,
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
            if tboxNo == hp.DEFAULT_INT:
                continue
            
            # 計算各村里的票數總和
            vill_list = hp.mapping_tbox.get(county_code, {}).get(town_code, {}).get(str(tboxNo), [])
            for vill_name in vill_list:
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

def generate_map_country_seats(raw_data, helper=hp.helper):
    '''
    Input:
        raw_data - running.json or final.json
    Output:
        result - [{election_type: seats_data}]
    '''
    result = {}
    all_seats = {}
    mapping_relationship = {
        'plain-indigenous': hp.mapping_plain_cand,
        'mountain-indigenous': hp.mapping_mountain_cand,
        'party': hp.mapping_party_seat,
    }
    ### 先計算山地原住民與平地原住民
    for election_type in ['plain-indigenous', 'mountain-indigenous']:
        calc_victors = 0
        election_data = raw_data[helper[election_type]][0] ### we only take the country data
        mapping_json = mapping_relationship[election_type]
        raw_candidates = election_data['candTksInfo']
        
        ### Calculate the candidate
        calc_seats = {}
        whole_seats = helper[f'{election_type}-allseats']
        for candidate in raw_candidates:
            candNo = candidate.get('candNo', hp.DEFAULT_INT)
            candInfo = mapping_json.get(str(candNo), None)
            if candInfo == None:
                continue
            addVictor = 1 if candidate.get('candVictor', ' ')=='*' else 0
            calc_victors += addVictor
            label = candInfo.get('party', '無黨籍及未經政黨推薦')
            if label == None:
                label = '無黨籍及未經政黨推薦'
            calc_seats[label] = calc_seats.get(label, 0) + addVictor
        
        ### Store into template
        seat_template = tp.SeatTemplate().to_json()
        for label, seats in calc_seats.items():
            if label==None:
                continue
            seat_checked = tp.SeatCandidateTemplate(label=label, seats=seats).to_json()
            seat_template['parties'].append(seat_checked)
            all_seats[label] = all_seats.get(label, 0) + seats
        seat_unchecked = 0 if (whole_seats-calc_victors)<0 else (whole_seats-calc_victors)
        seat_unchecked_template = tp.SeatCandidateTemplate(label=hp.UNDETERMINED_INFO, seats=seat_unchecked).to_json()
        seat_template['parties'].append(seat_unchecked_template)
        result[election_type] = seat_template

    ### 計算不分區立委(直接從final_A抓資料)
    calc_victors = 0
    election_type = 'party'
    seat_template = tp.SeatTemplate().to_json()
    whole_seats = helper[f'{election_type}-allseats']
    mapping_json  = mapping_relationship[election_type]
    for _, patyData in mapping_json.items():
        label = patyData.get('name', '無黨籍及未經政黨推薦')
        seats = patyData.get('seat', 0)
        seat_checked = tp.SeatCandidateTemplate(label=label, seats=seats).to_json()
        seat_template['parties'].append(seat_checked)
        all_seats[label] = all_seats.get(label, 0) + seats
        calc_victors += seats
    seat_unchecked = 0 if (whole_seats-calc_victors)<0 else (whole_seats-calc_victors)
    seat_unchecked_template = tp.SeatCandidateTemplate(label=hp.UNDETERMINED_INFO, seats=seat_unchecked).to_json()
    seat_template['parties'].append(seat_unchecked_template)
    result[election_type] = seat_template
    return result, all_seats

def generate_map_normal_seats(raw_data, helper=hp.helper):
    '''
    依照縣市(county)產生區域立委的席次表
    '''
    result = {}
    all_seats = {}
    parsed_county = parser.parse_county(raw_data, election_type='normal')
    for county_code, county_data in parsed_county['districts'].items():
        ### calculate the winner number of each party for the county
        seat_template = tp.SeatTemplate().to_json()
        seat_table = {}
        only_one_area = True if len(county_data)==1 else False
        for area_data in county_data:
            area_code = area_data.get('areaCode', hp.DEFAULT_AREACODE)
            if only_one_area==True:
                area_code = '01'
            area_candidates = hp.mapping_constituency_cand.get(county_code, {}).get(area_code, None)
            raw_candidates = area_data.get('candTksInfo', hp.DEFAULT_LIST)
            for candidate in raw_candidates:
                candNo    = candidate.get('candNo', hp.DEFAULT_INT)
                is_winner = candidate.get('candVictor', False)==True or candidate.get('candVictor', ' ')=='*'
                if is_winner==True:
                    party = area_candidates.get(str(candNo), {}).get('party', '無黨籍及未經政黨推薦')
                    if party == None:
                        party = '無黨籍及未經政黨推薦'
                    seat_table[party] = seat_table.get(party, 0) + 1
                    all_seats[party] = all_seats.get(party, 0) + 1
        seat_candidates_count = 0
        for party, seats in seat_table.items():
            seat_candidates_count += seats
            seat_cand = tp.SeatCandidateTemplate(label=party, seats=seats).to_json()
            seat_template['parties'].append(seat_cand)
        area_candidates_num =  len(hp.mapping_constituency_cand.get(county_code, {}))
        seat_cand = tp.SeatCandidateTemplate(label=hp.UNDETERMINED_INFO, seats=(area_candidates_num - seat_candidates_count)).to_json()
        seat_template['parties'].append(seat_cand)
        result[f'{county_code}.json'] = seat_template
    return result, all_seats

def generate_map_all_seats(seats_country, seats_normal, helper=hp.helper):
    ### 計算總席次
    election_type = 'all'
    seat_template = tp.SeatTemplate().to_json()
    whole_seats = helper[f'{election_type}-allseats']

    ### 統計席次總數
    calc_seats  = 0
    all_seats = {}
    for label, seats in seats_country.items():
        calc_seats += seats
        all_seats[label] = seats
    for label, seats in seats_normal.items():
        calc_seats += seats
        all_seats[label] = all_seats.get(label, 0) + seats

    ### 存入template
    for label, seats in all_seats.items():
        seat_checked = tp.SeatCandidateTemplate(label=label, seats=seats).to_json()
        seat_template['parties'].append(seat_checked)
    seat_unchecked = 0 if (whole_seats-calc_seats)<0 else (whole_seats-calc_seats)
    seat_unchecked_template = tp.SeatCandidateTemplate(label=hp.UNDETERMINED_INFO, seats=seat_unchecked).to_json()
    seat_template['parties'].append(seat_unchecked_template)
    return seat_template