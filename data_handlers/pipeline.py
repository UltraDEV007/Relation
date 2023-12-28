import os
import data_handlers.parser    as parser
import data_handlers.president.generator as pd_generator
import data_handlers.legislator.generator as lg_generator

import data_handlers.queries as query
import data_handlers.v2.adapter as v2_adapter
import data_handlers.v2.generator as v2_generator
import data_handlers.helpers as hp

from tools.uploadGCS import upload_blob, save_file, upload_blob_realtime
from datetime import datetime
import time

gql_endpoint = os.environ['GQL_URL']

'''
    V2: pipeline_v2會產生所有V2的資料
'''
def pipeline_v2(raw_data, seats_data, year:str, upload: bool=False):
    root_path = os.path.join(os.environ['ENV_FOLDER'], 'v2', '2024')

    ### Check the record execution time
    cec_time    = int(raw_data['ST'])
    record_time = hp.RECORD_EXECUTION_TIME['v2']
    if cec_time <= record_time:
        return False

    ### Generate the v2 president data
    mapping_president =  v2_adapter.adapter_president_v2()
    v2_president = v2_generator.generate_v2_president(raw_data, mapping_president, year)

    filename = os.path.join(root_path, 'president', 'all.json')
    save_file(filename, v2_president)
    if upload:
        upload_blob_realtime(filename)
    print(f'[V2] president data successed. Upload={upload}')

    ### Generate the v2 special legislator data(mountainIndigeous and plainIndigeous)
    # Plain 
    gql_plain_indigeous = query.gql2json(gql_endpoint, query.gql_plainIndigeous_2024)
    mapping_plain_indigeous = v2_adapter.adapter_indigeous_v2(gql_plain_indigeous)
    v2_plain_indigeous = v2_generator.generate_v2_special_legislator(
        raw_data,
        'legislator-plainIndigenous', 
        mapping_plain_indigeous, 
        year
    )

    filename = os.path.join(root_path, 'legislator', 'plainIndigenous','all.json')
    save_file(filename, v2_plain_indigeous)
    if upload:
        upload_blob_realtime(filename)
    print(f'[V2] Plain indigeous legislator data successed. Upload={upload}')
    
    # Mountain
    gql_mountain_indigeous = query.gql2json(gql_endpoint, query.gql_mountainIndigeous_2024)
    mapping_mountain_indigeous = v2_adapter.adapter_indigeous_v2(gql_mountain_indigeous)
    v2_mountain_indigeous = v2_generator.generate_v2_special_legislator(
        raw_data,
        'legislator-mountainIndigenous',
        mapping_mountain_indigeous, 
        year
    )

    filename = os.path.join(root_path, 'legislator', 'mountainIndigenous','all.json')
    save_file(filename, v2_mountain_indigeous)
    if upload:
        upload_blob_realtime(filename)
    print(f'[V2] Mountain indigeous legislator data successed. Upload={upload}')

    ### Generate the v2 party legislator data
    gql_party = query.gql2json(gql_endpoint, query.gql_party_2024)
    mapping_party = v2_adapter.adapter_party_v2(gql_party)
    if seats_data:
        parser.parse_seat(seats_data, mapping_party)
    v2_party = v2_generator.generate_v2_party_legislator(raw_data, mapping_party, year)

    filename = os.path.join(root_path, 'legislator', 'party','all.json')
    save_file(filename, v2_party)
    if upload:
        upload_blob_realtime(filename)
    print(f'[V2] Party legislator data successed. Upload={upload}')

    ### Generate the v2 constituency legislator data, you don't need to pass the mapping file
    v2_district = v2_generator.generate_v2_district_legislator(raw_data, year)
    districtRoot = os.path.join(root_path, 'legislator', 'district')
    for districtName, districtData in v2_district.items():
        filename = os.path.join(districtRoot, districtName)
        save_file(filename, districtData)
        if upload:
            upload_blob_realtime(filename)
    print(f'[V2] Constituency district data successed. Upload={upload}')

    hp.RECORD_EXECUTION_TIME['v2'] = cec_time
    return True

'''
    Map: pipeline_map_2024
    warning: 由於地圖的資料量較大，建議拆分成多個endpoint來實作
'''
def pipeline_map_2024(raw_data, is_started: bool=True, is_running: bool=False, upload: bool=False):
    '''
        raw_data - running.json or final.json
        upload   - True:單次上傳(upload_blob), False:批次上傳(upload_multiple)
    '''
    result = True

    ### Generate data for president
    result = pipeline_president_2024(
        raw_data, 
        is_started = is_started,
        is_running = is_running,
        upload = upload,
    )
    if result==False:
        print("No new president map data generated")

    ### Generate data for legislator
    result = pipeline_legislator_constituency_2024(
        raw_data,
        is_started = is_started,
        is_running = is_running,
        upload = upload,
    )
    if result==False:
        print("No new constituency map data generated")

    result = pipeline_legislator_indigeous_2024(
        raw_data,
        is_started = is_started,
        is_running = is_running,
        upload = upload,
    )
    if result==False:
        print("No new indigeous map data generated")

    result = pipeline_legislator_party_2024(
        raw_data,
        is_started=is_started,
        is_running=is_running,
        upload = upload,
    )
    if result==False:
        print("No new party map data generated")

    ### TODO: Upload all the data using gsutil

    return result

def pipeline_president_2024(raw_data, is_started: bool=True, is_running: bool=False, upload=False):
    prev_time = time.time()
    root_path = os.path.join(os.environ['ENV_FOLDER'], '2024', 'president', 'map')
    
    ### Check the record execution time
    cec_time    = int(raw_data['ST'])
    record_time = hp.RECORD_EXECUTION_TIME['map']['president']
    if cec_time <= record_time:
        return False
    
    ### Parse and store country
    parsed_county = parser.parse_county(raw_data, election_type='president')
    country_json  = pd_generator.generate_country_json(
        preprocessing_data = parsed_county, 
        is_running = is_running,
        is_started = is_started    
    )
    filename = os.path.join(root_path, 'country', 'country.json')
    save_file(filename, country_json)
    if upload:
        upload_blob_realtime(filename)

    ### Parse and store county
    generated_county_json = pd_generator.generate_county_json(
        preprocessing_data = parsed_county,
        is_running = is_running,
        is_started = is_started
    )
    for county_code, county_json in generated_county_json.items():
        filename = os.path.join(root_path, 'county', county_code)
        save_file(filename, county_json)
        if upload:
            upload_blob_realtime(filename)

    ### Parse town
    if is_running == False:
        county_codes = list(parsed_county['districts'].keys())       
        result = []
        updateAt = parsed_county.get('updateAt', None)
        for county_code in county_codes:
            if county_code in hp.NO_PROCESSING_CODE:
                continue
            county_data         = parsed_county['districts'].get(county_code, None)
            town_data           = parser.parse_town(county_code, county_data)
            vill_data, errors   = pd_generator.generate_town_json(town_data, updateAt, is_running, is_started)
            result.append(vill_data)
            # You can use errors to track the problematic tboxNo
        for vill_data in result:
            for key, value in vill_data.items():
                filename = os.path.join(root_path, 'town', key)
                save_file(filename, value)
                if upload:
                    upload_blob_realtime(filename)
    cur_time = time.time()
    exe_time = round(cur_time-prev_time, 2)
    print(f'[MAP] President costed {exe_time} sec, is_running={is_running}')
    hp.RECORD_EXECUTION_TIME['map']['president'] = cec_time
    return True

def pipeline_legislator_constituency_2024(raw_data, is_started: bool=True, is_running: bool=False, upload=False):
    prev_time = time.time()
    if is_running:
        return False ### We don't deal with constituency data when it's not final.json
    
    ### Check the record execution time
    cec_time    = int(raw_data['ST'])
    record_time = hp.RECORD_EXECUTION_TIME['map']['constituency']
    if cec_time <= record_time:
        return False

    ### Generate the data for constituency
    root_path = os.path.join(os.environ['ENV_FOLDER'], '2024', 'legislator', 'map', 'constituency', 'normal')
    parsed_area = parser.parse_constituency_area(raw_data)
    constituency_result = lg_generator.generate_constituency_json(parsed_area, is_running, is_started)
    for name, data in constituency_result.items():
        filename = os.path.join(root_path, name)
        save_file(filename, data)
        if upload:
            upload_blob_realtime(filename)
    cur_time = time.time()
    exe_time = round(cur_time-prev_time, 2)
    print(f'[MAP] Legislator constituency costed {exe_time} sec, is_running={is_running}')
    hp.RECORD_EXECUTION_TIME['map']['constituency'] = cec_time
    return True

def pipeline_legislator_indigeous_2024(raw_data, is_started: bool=True, is_running: bool=False, upload: bool=False):
    '''
        In this pipeline, we generate mountain and plain indigenous in one pipeline
    '''
    prev_time = time.time()
    root_path = os.path.join(os.environ['ENV_FOLDER'], '2024', 'legislator', 'map')
    
    ### Check the record execution time
    cec_time    = int(raw_data['ST'])
    record_time = hp.RECORD_EXECUTION_TIME['map']['indigeous']
    if cec_time <= record_time:
        return False
    
    for election_type in ['mountainIndigenous', 'plainIndigenous']:
        parsed_county = parser.parse_county(raw_data, election_type)

        ### Generate country
        country_json  = lg_generator.generate_country_json(parsed_county, is_running, is_started, election_type)
        filename = os.path.join(root_path, 'country', election_type, 'country.json')
        save_file(filename, country_json)
        if upload:
            upload_blob_realtime(filename)

        ### Generate county
        county_result = lg_generator.generate_county_json(parsed_county, is_running, is_started, election_type)
        for name, county_json in county_result.items():
            filename = os.path.join(root_path, 'county', election_type, name)
            save_file(filename, county_json)
            if upload:
                upload_blob_realtime(filename)
        
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
                vill_data   = lg_generator.generate_town_json(town_data, updateAt, is_running, True, election_type)
                vill_result.append(vill_data)
            
            for vill_data in vill_result:
                for name, value in vill_data.items():
                    filename = os.path.join(root_path, 'town', election_type, name)
                    save_file(filename, value)
                    if upload:
                        upload_blob_realtime(filename)
    cur_time = time.time()
    exe_time = round(cur_time-prev_time, 2)
    print(f'[MAP] Legislator special(mountain&plain) costed {exe_time} sec, is_running={is_running}')
    hp.RECORD_EXECUTION_TIME['map']['indigeous'] = cec_time
    return True

def pipeline_legislator_party_2024(raw_data, is_started: bool=True, is_running: bool=False, upload: bool=False):
    prev_time = time.time()
    root_path = os.path.join(os.environ['ENV_FOLDER'], '2024', 'legislator', 'map')
    election_type = 'party'

    ### Check the record execution time
    cec_time    = int(raw_data['ST'])
    record_time = hp.RECORD_EXECUTION_TIME['map']['party']
    if cec_time <= record_time:
        return False

    ### Generate country
    parsed_county = parser.parse_county(raw_data, election_type)
    country_json  = lg_generator.generate_country_json(parsed_county, is_running, is_started, election_type)
    filename = os.path.join(root_path, 'country', election_type, 'country.json')
    save_file(filename, country_json)
    if upload:
        upload_blob_realtime(filename)

    ### Generate county
    county_result = lg_generator.generate_county_json(parsed_county, is_running, is_started, election_type)
    for name, county_json in county_result.items():
        filename = os.path.join(root_path, 'county', election_type, name)
        save_file(filename, county_json)
        if upload:
            upload_blob_realtime(filename)

    ### Generate town
    county_codes = list(parsed_county['districts'].keys())
    updateAt = parsed_county['updateAt']

    vill_result = []
    for county_code in county_codes:
        if county_code in hp.NO_PROCESSING_CODE:
            continue
        county_data = parsed_county['districts'].get(county_code, None)
        town_data   = parser.parse_town(county_code, county_data)
        vill_data   = lg_generator.generate_town_json(town_data, updateAt, is_running, True, election_type)
        vill_result.append(vill_data)
    
    for vill_data in vill_result:
        for name, value in vill_data.items():
            filename = os.path.join(root_path, 'town', election_type, name)
            save_file(filename, value)
            if upload:
                upload_blob_realtime(filename)
    cur_time = time.time()
    exe_time = round(cur_time-prev_time, 2)
    print(f'[MAP] Legislator party costed {exe_time} sec, is_running={is_running}')
    hp.RECORD_EXECUTION_TIME['map']['party'] = cec_time
    return True

