import os
import data_handlers.parser    as parser
import data_handlers.map.generator as map_generator

import data_handlers.gql.query as query
from data_handlers.gql.tool import gql_fetch

import data_handlers.v2.adapter as v2_adapter
import data_handlers.v2.generator as v2_generator
import data_handlers.helpers as hp
import data_handlers.templates as tp

from tools.uploadGCS import save_file, upload_blob_realtime, upload_folder_async, open_file
import time
import copy

gql_endpoint = os.environ['GQL_URL']

'''
    V2: pipeline_v2會產生所有V2的資料
'''
def pipeline_v2(raw_data, seats_data, year:str, is_running: bool=False):
    root_path = os.path.join(os.environ['ENV_FOLDER'], 'v2', '2024')

    ### Generate the v2 president data
    gql_presidents = gql_fetch(gql_endpoint, query.gql_president_2024)
    mapping_president =  v2_adapter.adapter_president_v2(gql_presidents)
    v2_president = v2_generator.generate_v2_president(raw_data, mapping_president, year)

    filename = os.path.join(root_path, 'president', 'all.json')
    save_file(filename, v2_president)
    if is_running==True:
        upload_blob_realtime(filename)
    print(f'[V2] president data successed.')

    ### Generate the v2 special legislator data(mountainIndigeous and plainIndigeous)
    # Plain 
    gql_plain_indigeous = gql_fetch(gql_endpoint, query.gql_plainIndigeous_2024)
    mapping_plain_indigeous = v2_adapter.adapter_indigeous_v2(gql_plain_indigeous)
    v2_plain_indigeous = v2_generator.generate_v2_special_legislator(
        raw_data,
        'legislator-plainIndigenous', 
        mapping_plain_indigeous, 
        year
    )

    filename = os.path.join(root_path, 'legislator', 'plainIndigenous','all.json')
    save_file(filename, v2_plain_indigeous)
    if is_running==True:
        upload_blob_realtime(filename)
    print(f'[V2] Plain indigeous legislator data successed.')
    
    # Mountain
    gql_mountain_indigeous = gql_fetch(gql_endpoint, query.gql_mountainIndigeous_2024)
    mapping_mountain_indigeous = v2_adapter.adapter_indigeous_v2(gql_mountain_indigeous)
    v2_mountain_indigeous = v2_generator.generate_v2_special_legislator(
        raw_data,
        'legislator-mountainIndigenous',
        mapping_mountain_indigeous, 
        year
    )

    filename = os.path.join(root_path, 'legislator', 'mountainIndigenous','all.json')
    save_file(filename, v2_mountain_indigeous)
    if is_running==True:
        upload_blob_realtime(filename)
    print(f'[V2] Mountain indigeous legislator data successed.')

    ### Generate the v2 party legislator data
    gql_party = gql_fetch(gql_endpoint, query.gql_party_oe_2024)
    mapping_party = v2_adapter.adapter_party_v2(gql_party)
    if seats_data:
        parser.parse_seat(seats_data, mapping_party)
    v2_party = v2_generator.generate_v2_party_legislator(raw_data, mapping_party, year)

    filename = os.path.join(root_path, 'legislator', 'party','all.json')
    save_file(filename, v2_party)
    if is_running==True:
        upload_blob_realtime(filename)
    print(f'[V2] Party legislator data successed.')

    ### Generate the v2 constituency legislator data, you don't need to pass the mapping file
    v2_district = v2_generator.generate_v2_district_legislator(raw_data, is_running, year)
    districtRoot = os.path.join(root_path, 'legislator', 'district')
    for districtName, districtData in v2_district.items():
        filename = os.path.join(districtRoot, districtName)
        save_file(filename, districtData)
        if is_running==True:
            upload_blob_realtime(filename)
    print(f'[V2] Constituency district data successed.')

    return True

'''
    Map: pipeline_map_2024
'''
def pipeline_map_2024(raw_data, is_started: bool=True, is_running: bool=False):
    '''
    Description:
        Generate the election data for 2024, including president, legislator(constituency, indigeous, party)
    Input:
        raw_data - running.json or final.json
    '''
    result = True

    ### Generate data for president
    result = pipeline_president_2024(
        raw_data, 
        is_started = is_started,
        is_running = is_running,
    )
    if result==False:
        print("No new president map data generated")

    ### Generate data for legislator
    result = pipeline_legislator_constituency_2024(
        raw_data,
        is_started = is_started,
        is_running = is_running,
    )
    if result==False:
        print("No new constituency map data generated")

    result = pipeline_legislator_indigeous_2024(
        raw_data,
        is_started = is_started,
        is_running = is_running,
    )
    if result==False:
        print("No new indigeous map data generated")

    result = pipeline_legislator_party_2024(
        raw_data,
        is_started=is_started,
        is_running=is_running,
    )
    if result==False:
        print("No new party map data generated")

    return result

def pipeline_president_2024(raw_data, is_started: bool=True, is_running: bool=False):
    election_type = 'president'
    prev_time = time.time()
    root_path = os.path.join(os.environ['ENV_FOLDER'], '2024', 'president', 'map')
    
    ### Parse and store country(For country level, we'll upload immediately)
    parsed_county = parser.parse_county(raw_data, election_type='president')
    country_json  = map_generator.generate_country_json(
        preprocessing_data = parsed_county, 
        is_running = is_running,
        is_started = is_started,
        election_type = election_type,
    )
    filename = os.path.join(root_path, 'country', 'country.json')
    save_file(filename, country_json)
    if is_running==True:
        upload_blob_realtime(filename)

    ### Parse and store county
    generated_county_json = map_generator.generate_county_json(
        preprocessing_data = parsed_county,
        is_running = is_running,
        is_started = is_started,
        election_type = election_type,
    )
    folder = os.path.join(root_path, 'county')
    for county_code, county_json in generated_county_json.items():
        filename = os.path.join(folder, county_code)
        save_file(filename, county_json)

    ### Parse town
    if is_running == False:
        county_codes = list(parsed_county['districts'].keys())       
        result = []
        updateAt = parsed_county.get('updateAt', None)
        folder = os.path.join(root_path, 'town')
        for county_code in county_codes:
            if county_code in hp.NO_PROCESSING_CODE:
                continue
            county_data   = parsed_county['districts'].get(county_code, None)
            town_data     = parser.parse_town(county_code, county_data)
            vill_data     = map_generator.generate_town_json(town_data, updateAt, is_running, is_started, election_type)
            result.append(vill_data)
            # You can use errors to track the problematic tboxNo
        for vill_data in result:
            for key, value in vill_data.items():
                filename = os.path.join(folder, key)
                save_file(filename, value)
    cur_time = time.time()
    exe_time = round(cur_time-prev_time, 2)
    print(f'[MAP] President costed {exe_time} sec, is_running={is_running}')
    return True

def pipeline_legislator_constituency_2024(raw_data, is_started: bool=True, is_running: bool=False):
    prev_time = time.time()
    election_type = 'normal'

    ### Generate county data
    parsed_county = parser.parse_county(raw_data, election_type=election_type)
    generated_county_json = map_generator.generate_constituency_county_json(
        preprocessing_data = parsed_county,
        is_running = is_running,
        is_started = is_started,
    )

    folder = os.path.join(os.environ['ENV_FOLDER'], '2024', 'legislator', 'map', 'county', election_type)
    for county_code, county_json in generated_county_json.items():
        filename = os.path.join(folder, county_code)
        save_file(filename, county_json)

    ### Generate town data
    if is_running:
        print("We don't generate constituency town data when file is running.json")
        return False
    folder = os.path.join(os.environ['ENV_FOLDER'], '2024', 'legislator', 'map', 'constituency', election_type)
    parsed_area = parser.parse_constituency_area(raw_data)
    constituency_result = map_generator.generate_constituency_town_json(parsed_area, is_running, is_started)
    for name, data in constituency_result.items():
        filename = os.path.join(folder, name)
        save_file(filename, data)

    cur_time = time.time()
    exe_time = round(cur_time-prev_time, 2)
    print(f'[MAP] Legislator constituency costed {exe_time} sec, is_running={is_running}')
    return True

def pipeline_legislator_indigeous_2024(raw_data, is_started: bool=True, is_running: bool=False):
    '''
        In this pipeline, we generate mountain and plain indigenous in one pipeline
    '''
    prev_time = time.time()
    root_path = os.path.join(os.environ['ENV_FOLDER'], '2024', 'legislator', 'map')
    
    for election_type in ['mountainIndigenous', 'plainIndigenous']:
        parsed_county = parser.parse_county(raw_data, election_type)
        upload_folder = 'mountain-indigenous' if election_type == 'mountainIndigenous' else 'plain-indigenous'

        ### Generate country(upload immediately)
        country_json  = map_generator.generate_country_json(parsed_county, is_running, is_started, election_type)
        filename = os.path.join(root_path, 'country', upload_folder, 'country.json')
        save_file(filename, country_json)
        if is_running==True:
            upload_blob_realtime(filename)

        ### Generate county
        folder = os.path.join(root_path, 'county', upload_folder)
        county_result = map_generator.generate_county_json(parsed_county, is_running, is_started, election_type)
        for name, county_json in county_result.items():
            filename = os.path.join(folder, name)
            save_file(filename, county_json)
        
        ### Generate town(only in final.json)
        if is_running==False:
            county_codes = list(parsed_county['districts'].keys())
            updateAt = parsed_county['updateAt']

            vill_result = []
            for county_code in county_codes:
                if county_code in hp.NO_PROCESSING_CODE:
                    continue
                county_data = parsed_county['districts'].get(county_code, None)
                town_data   = parser.parse_town(county_code, county_data)
                vill_data   = map_generator.generate_town_json(town_data, updateAt, is_running, True, election_type)
                vill_result.append(vill_data)
            
            folder = os.path.join(root_path, 'town', upload_folder)
            for vill_data in vill_result:
                for name, value in vill_data.items():
                    filename = os.path.join(folder, name)
                    save_file(filename, value)
    cur_time = time.time()
    exe_time = round(cur_time-prev_time, 2)
    print(f'[MAP] Legislator special(mountain&plain) costed {exe_time} sec, is_running={is_running}')
    return True

def pipeline_legislator_party_2024(raw_data, is_started: bool=True, is_running: bool=False):
    prev_time = time.time()
    root_path = os.path.join(os.environ['ENV_FOLDER'], '2024', 'legislator', 'map')
    election_type = 'party'

    ### Generate country(upload immediately)
    parsed_county = parser.parse_county(raw_data, election_type)
    country_json  = map_generator.generate_country_json(parsed_county, is_running, is_started, election_type)
    filename = os.path.join(root_path, 'country', election_type, 'country.json')
    save_file(filename, country_json)
    if is_running==True:
        upload_blob_realtime(filename)

    ### Generate county
    folder = os.path.join(root_path, 'county', election_type)
    county_result = map_generator.generate_county_json(parsed_county, is_running, is_started, election_type)
    for name, county_json in county_result.items():
        filename = os.path.join(folder, name)
        save_file(filename, county_json)

    ### Generate town
    if is_running==False:
        county_codes = list(parsed_county['districts'].keys())
        updateAt = parsed_county['updateAt']

        vill_result = []
        for county_code in county_codes:
            if county_code in hp.NO_PROCESSING_CODE:
                continue
            county_data = parsed_county['districts'].get(county_code, None)
            town_data   = parser.parse_town(county_code, county_data)
            vill_data   = map_generator.generate_town_json(town_data, updateAt, is_running, True, election_type)
            vill_result.append(vill_data)
        
        folder = os.path.join(root_path, 'town', election_type)
        for vill_data in vill_result:
            for name, value in vill_data.items():
                filename = os.path.join(folder, name)
                save_file(filename, value)
    cur_time = time.time()
    exe_time = round(cur_time-prev_time, 2)
    print(f'[MAP] Legislator party costed {exe_time} sec, is_running={is_running}')
    return True

def pipeline_map_seats(raw_data, is_running):
    prev_time = time.time()
    folder = os.path.join(os.environ['ENV_FOLDER'], '2024', 'legislator', 'seat')

    ### 產生全國席次表
    result, seats_country = map_generator.generate_map_country_seats(raw_data)
    country_list = ['mountain-indigenous', 'plain-indigenous', 'party']
    for election_type, election_data in result.items():
        if election_type in country_list:
            filename = os.path.join(folder, 'country', election_type, 'country.json')
            save_file(filename, election_data)
            if is_running==True:
                upload_blob_realtime(filename)
    
    ### 產生縣市席次表(僅有區域立委Constituency)
    result, seats_normal = map_generator.generate_map_normal_seats(raw_data)
    for county_name, county_data in result.items():
        filename = os.path.join(folder, 'county', 'normal', county_name)
        save_file(filename, county_data)
        if is_running==True:
            upload_blob_realtime(filename)

    ### 產生席次表統整
    all_json = map_generator.generate_map_all_seats(seats_country, seats_normal)
    filename = os.path.join(folder, 'country', 'all', 'country.json')
    save_file(filename, all_json)
    if is_running==True:
        upload_blob_realtime(filename)

    cur_time = time.time()
    exe_time = round(cur_time-prev_time, 2)
    print(f'[MAP] Map seats costed {exe_time} sec')
    return True

'''
    Default: 建立在選舉開始前的預設資料
'''
def pipeline_default_map(updatedAt: str=None, is_running: bool=False, is_started: bool=False):
    root_path = os.path.join(os.environ['ENV_FOLDER'], '2024')
    default_country = tp.getDefaultCountry(updatedAt, is_running, is_started)
    default_county  = tp.getDefaultCounty(updatedAt, is_running, is_started)
    default_town    = tp.getDefaultTown(updatedAt, is_running, is_started)
    default_constituency = tp.getDefaultConstituency(updatedAt, is_running, is_started)
    
    ### Save default country
    # For president
    filename = os.path.join(root_path, 'president', 'map', 'country', 'country.json')
    save_file(filename, default_country)
    # For legislators
    path = os.path.join(root_path, 'legislator', 'map', 'country')
    for election_type in ['party', 'mountain-indigenous', 'plain-indigenous']:
        filename = os.path.join(path, election_type, 'country.json')
        save_file(filename, default_county)

    ### Save default county
    for county_code in list(hp.mapping_city.keys()):
        if county_code in hp.NO_PROCESSING_CODE:
            continue
        # For president
        filename = os.path.join(root_path, 'president', 'map', 'county', f'{county_code}.json')
        save_file(filename, default_county)
        # For legislators
        path = os.path.join(root_path, 'legislator', 'map', 'county')
        for election_type in ['party', 'normal', 'mountain-indigenous', 'plain-indigenous']:
            filename = os.path.join(path, election_type, f'{county_code}.json')
            save_file(filename, default_county)

    ### Save default town(except constituency)
    for code in list(hp.mapping_town.keys()):
        county_code = code[:hp.COUNTY_CODE_LENGTH]
        town_code   = code[hp.COUNTY_CODE_LENGTH:]
        if (town_code[-1]!='0') or (town_code==hp.DEFAULT_TOWNCODE) or (county_code in hp.NO_PROCESSING_CODE):
            continue
        # For president
        filename = os.path.join(root_path, 'president', 'map', 'town', f'{code}.json')
        save_file(filename, default_town)
        # For legislators
        path = os.path.join(root_path, 'legislator', 'map', 'town')
        for election_type in ['party', 'mountain-indigenous', 'plain-indigenous']:
            filename = os.path.join(path, election_type, f'{code}.json')
            save_file(filename, default_town)
    
    ### Save default area(constituency)
    path = os.path.join(root_path, 'legislator', 'map', 'constituency', 'normal')
    for county_code, area_data in hp.mapping_constituency_cand.items():
        for area_code, _ in area_data.items():
            filename = os.path.join(path, f'{county_code}{area_code}.json')
            save_file(filename, default_constituency)
    return "ok"

def pipeline_map_modify(is_running, is_started):
    root_path = os.path.join(os.environ['ENV_FOLDER'], '2024')
    def modify_info(data, is_running, is_started):
        new_data = copy.deepcopy(data)
        new_data['is_running'] = is_running
        new_data['is_started'] = is_started
        return new_data

    ### Save default country
    # For president
    filename = os.path.join(root_path, 'president', 'map', 'country', 'country.json')
    country_json = open_file(filename)
    if country_json:
        save_file(filename, modify_info(country_json, is_running, is_started))

    # For legislators
    path = os.path.join(root_path, 'legislator', 'map', 'country')
    for election_type in ['party', 'mountain-indigenous', 'plain-indigenous']:
        filename = os.path.join(path, election_type, 'country.json')
        country_json = open_file(filename)
        if country_json:
            save_file(filename, modify_info(country_json, is_running, is_started))
    
    ### Save default county
    for county_code in list(hp.mapping_city.keys()):
        if county_code in hp.NO_PROCESSING_CODE:
            continue
        # For president
        filename = os.path.join(root_path, 'president', 'map', 'county', f'{county_code}.json')
        county_json = open_file(filename)
        if county_json:
            save_file(filename, modify_info(county_json, is_running, is_started))

        # For legislators
        path = os.path.join(root_path, 'legislator', 'map', 'county')
        for election_type in ['party', 'normal', 'mountain-indigenous', 'plain-indigenous']:
            filename = os.path.join(path, election_type, f'{county_code}.json')
            county_json = open_file(filename)
            if county_json:
                save_file(filename, modify_info(county_json, is_running, is_started))

    ### Save default town(except constituency)
    for code in list(hp.mapping_town.keys()):
        county_code = code[:hp.COUNTY_CODE_LENGTH]
        town_code   = code[hp.COUNTY_CODE_LENGTH:]
        if (town_code[-1]!='0') or (town_code==hp.DEFAULT_TOWNCODE) or (county_code in hp.NO_PROCESSING_CODE):
            continue
        # For president
        filename = os.path.join(root_path, 'president', 'map', 'town', f'{code}.json')
        town_json = open_file(filename)
        if town_json:
            save_file(filename, modify_info(town_json, is_running, is_started))
        # For legislators
        path = os.path.join(root_path, 'legislator', 'map', 'town')
        for election_type in ['party', 'mountain-indigenous', 'plain-indigenous']:
            filename = os.path.join(path, election_type, f'{code}.json')
            town_json = open_file(filename)
            if town_code:
                save_file(filename, modify_info(town_json, is_running, is_started))
    ### Save default area(constituency)
    path = os.path.join(root_path, 'legislator', 'map', 'constituency', 'normal')
    for county_code, area_data in hp.mapping_constituency_cand.items():
        for area_code, _ in area_data.items():
            filename = os.path.join(path, f'{county_code}{area_code}.json')
            area_json = open_file(filename)
            if area_json:
                save_file(filename, modify_info(area_json, is_running, is_started))
    return "ok"

def pipeline_default_seats():
    root_path = os.path.join(os.environ['ENV_FOLDER'], '2024', 'legislator', 'seat')
    
    ### Save default seats country
    for election_type in ['all', 'party', 'mountain-indigenous', 'plain-indigenous']:
        default_seats = tp.getDefaultSeat(election_type=election_type)
        filename = os.path.join(root_path, 'country', election_type, 'country.json')
        save_file(filename, default_seats)
    
    ### Save default seats county(only for normal)
    election_type = 'normal'
    for county_code, area_data in hp.mapping_constituency_cand.items():
        area_seats = len(area_data)
        default_seats = tp.getDefaultSeat(election_type=election_type, area_seats=area_seats)
        filename = os.path.join(root_path, 'county', election_type, f'{county_code}.json')
        save_file(filename, default_seats)
    return "ok"