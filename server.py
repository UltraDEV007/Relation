import os
import googleapiclient
from flask import Flask, request, json
from politics_dump import dump_politics, landing
from datetime import datetime
from tools.cec_data import request_cec_by_type, request_cec, request_url
from tools.uploadGCS import upload_multiple_folders, upload_multiple, upload_folder_async
from referendum import parse_cec_referendum, gen_referendum
from mayor import gen_mayor, parse_cec_mayor, parse_tv_sht, gen_tv_mayor
from councilMember import gen_councilMember, parse_cec_council
from election import factcheck_data, election2024, politics_dump
from data_export import president2024_realtime

import data_handlers.helpers as hp
import data_handlers.parser as parser
import data_handlers.update as gql_update

from data_handlers import pipeline
import time
import copy

app = Flask(__name__)

IS_TV =  os.environ['PROJECT'] == 'tv' 
IS_STARTED = os.environ['IS_STARTED'] == 'true'
BUCKET = os.environ['BUCKET']
ENV_FOLDER = os.environ['ENV_FOLDER']

### election 2024
@app.route('/elections/update/cms/<year>', methods=['POST'])
def election_update_cms(year):
    '''
        Fetch v2 json from bucket and update the result into CMS. 
        In the json payload, you should specify the <election_type> you want to update and <gen_term_offic> to 
        determine whether to generate term office period for winner.
    '''
    payload = json.loads(request.data)
    gen_term_office = payload.get('gen_term_office', False)
    ### person election
    election_types = ['president', 'mountainIndigenous', 'plainIndigenous']
    for election_type in election_types:
        if payload.get(election_type, False)==True:
            result = gql_update.update_person_election(year, election_type, gen_term_office)
            if result==False:
                print(f'Update cms {election_type} data failed.')

    ### party election
    if payload.get('party', False)==True:
        result = gql_update.update_party_election(year, gen_term_office)
        if result==False:
            print(f'Update cms party data failed')

    ### normal election
    if payload.get('normal', False)==True:
        result = gql_update.update_normal_election(year, gen_term_office)
        if result==False:
            print(f'Update cms normal data failed')
    return "ok"

@app.route('/elections/all/2024', methods=['POST'])
def election_all_2024():
    '''
        Generate both map and v2 data in one batch
    '''
    if IS_STARTED:
        prev_time = time.time()
        seats_data = request_cec('final_A.json')
        raw_data, is_running = request_cec_by_type()
        if seats_data:
            print('Receive final_A data, write the seats information')
            parser.parse_seat(seats_data, hp.mapping_party_seat)
        cur_time = time.time()
        print(f'Time of fetching CEC data is {round(cur_time-prev_time,2)}s, is_running={is_running}')

        ### 修改default檔案(抓不到檔案時is_running會是None)
        if hp.MODIFY_START_DEFAULT==False and is_running==True:
            print('modify start default json')
            _ = pipeline.pipeline_map_modify(is_started=IS_STARTED, is_running=True)
            hp.MODIFY_START_DEFAULT = True
        if hp.MODIFY_FINAL_DEFAULT==False and is_running==False:
            print('modify final default json')
            _ = pipeline.pipeline_map_modify(is_started=IS_STARTED, is_running=False)
            hp.MODIFY_FINAL_DEFAULT = True

        ### 當raw_data存在時，表示有取得新一筆的資料，處理完後需上傳(若無新資料就不處理)
        prev_time = cur_time
        if raw_data:
            _ = pipeline.pipeline_map_seats(raw_data, is_running)
            _ = pipeline.pipeline_map_2024(raw_data, is_started = IS_STARTED, is_running=is_running)
            _ = pipeline.pipeline_v2(raw_data, seats_data, '2024', is_running=is_running)
            upload_multiple('2024', upload_map=True, upload_v2=(is_running!=True))
            cur_time = time.time()
            print(f'Time of map&v2 pipeline is {round(cur_time-prev_time,2)}s')
    return "ok"

@app.route('/elections/manual/<stage>', methods=['POST'])
def election_manual(stage):
    '''
        Generate running json manually, stage='running' or 'final'.
        Becareful, you should upload the json files previously into the BUCKET/ENV_FOLDER.
    '''
    if IS_STARTED:
        running_url = f'https://{BUCKET}/{ENV_FOLDER}/cec-data/running.json'
        final_url   = f'https://{BUCKET}/{ENV_FOLDER}/cec-data/final.json'
        final_A_url = f'https://{BUCKET}/{ENV_FOLDER}/cec-data/final_A.json'
        print(f'Create data manually, stage={stage}')

        if stage=='running':
            if hp.MODIFY_START_DEFAULT==False:
                _ = pipeline.pipeline_map_modify(is_started=IS_STARTED, is_running=True)
                hp.MODIFY_START_DEFAULT = True
            seats_data = None
            raw_data, is_running = request_url(running_url), True
            prev_time = time.time()
            if raw_data:
                _ = pipeline.pipeline_map_seats(raw_data, is_running)
                _ = pipeline.pipeline_map_2024(raw_data, is_started = IS_STARTED, is_running=is_running)
                _ = pipeline.pipeline_v2(raw_data, seats_data, '2024', is_running=is_running)
                upload_multiple('2024', upload_map=True, upload_v2=False)
                cur_time = time.time()
                print(f'Time of map&v2 pipeline is {round(cur_time-prev_time,2)}s, is_running={is_running}')
        if stage=='final':
            if hp.MODIFY_FINAL_DEFAULT==False:
                _ = pipeline.pipeline_map_modify(is_started=IS_STARTED, is_running=False)
                hp.MODIFY_FINAL_DEFAULT = True
            hp.mapping_party_seat = copy.deepcopy(hp.mapping_party_seat_init)
            seats_data = request_url(final_A_url)
            if seats_data:
                print('Receive final_A data, write the seats information')
                parser.parse_seat(seats_data, hp.mapping_party_seat)
            raw_data, is_running = request_url(final_url), False
            prev_time = time.time()
            if raw_data:
                _ = pipeline.pipeline_map_seats(raw_data, is_running)
                _ = pipeline.pipeline_map_2024(raw_data, is_started = IS_STARTED, is_running=is_running)
                _ = pipeline.pipeline_v2(raw_data, seats_data, '2024', is_running=is_running)
                upload_multiple('2024', upload_map=True, upload_v2=(is_running!=True))
                cur_time = time.time()
                print(f'Time of map&v2 pipeline is {round(cur_time-prev_time,2)}s, is_running={is_running}')
    return 'ok'

@app.route('/elections/default', methods=['POST'])
def election_all_default():
    '''
        Generate default jsons
    '''
    print('Create default json')
    hp.mapping_party_seat = copy.deepcopy(hp.mapping_party_seat_init)
    default_url  = f'https://{BUCKET}/{ENV_FOLDER}/cec-data/init.json'
    default_file = request_url(default_url)
    _ = pipeline.pipeline_default_map(is_started=False, is_running=False)
    _ = pipeline.pipeline_default_seats()
    if default_file:
        _ = pipeline.pipeline_map_2024(default_file, is_started=False, is_running=False)
        _ = pipeline.pipeline_v2(default_file, None, '2024', is_running=True) ### If is_running=False, we'll mark the winner
    upload_multiple('2024', upload_map=True, upload_v2=False)
    return "ok"

@app.route('/elections/modify/<stage>', methods=['POST'])
def election_modify(stage):
    '''
        Modify the IS_STARTED and IS_RUNNING columns in json and upload
    '''
    if stage=='running':
        print(f'modify running default json, original state={hp.MODIFY_START_DEFAULT}')
        _ = pipeline.pipeline_map_modify(is_started=IS_STARTED, is_running=True)
        hp.MODIFY_START_DEFAULT = True
        upload_multiple('2024', upload_map=True, upload_v2=False)
    if stage=='final':
        print(f'modify final default json, original state={hp.MODIFY_FINAL_DEFAULT}')
        _ = pipeline.pipeline_map_modify(is_started=IS_STARTED, is_running=False)
        hp.MODIFY_FINAL_DEFAULT = True
        upload_multiple('2024', upload_map=True, upload_v2=False)
    return "ok"

@app.route('/elections/cec/upload', methods=['POST'])
def cec_upload():
    '''
        Upload all the retrieved cec data during the execution time
    '''
    folder = os.path.join(ENV_FOLDER, 'cec-data')
    upload_folder_async(folder)
    return "ok"

@app.route("/election2024_homepage")
def election_homepage():
    realtime_data = president2024_realtime()
    return "ok"

### old version implementations
@app.route("/politics_data_dump")
def tracker_data_dump():
	politics_dump()
	return "ok"

@app.route("/president_factcheck")
def president_fackcheck_json():
	factcheck_data()
	election2024()
	return "ok"

@app.route("/elections_json_rf", methods=['GET'])
def elections_rf():
    '''
        Generate result for referendum(公投)
    '''
    year = datetime.now().year
    if IS_STARTED:
        referendumfile, is_running = request_cec_by_type('rf')
        if referendumfile:
            polling_data = parse_cec_referendum(referendumfile)
            updatedAt = datetime.strptime(referendumfile["ST"], '%m%d%H%M%S')
            updatedAt = f"{year}-{datetime.strftime(updatedAt, '%m-%d %H:%M:%S')}"
            gen_referendum(updatedAt, polling_data, is_running=is_running)
            print("referendum done")
        else:
            print('problem of cec referendum data ')
    else: # gen default data, like: name, no. and tks = 0
        gen_referendum()
        print("referendum done")
    upload_multiple_folders(year)
    return 'done'


@app.route("/gen_elections_json", methods=['GET'])
def elections():
    '''
        Generate result for elections
    '''
    year = datetime.now().year
    if IS_STARTED:
        # Fetch and parse election data if the election has started
        jsonfile, is_running = request_cec_by_type()
        if jsonfile:
            updatedAt = datetime.strptime(jsonfile["ST"], '%m%d%H%M%S')
            updatedAt = f"{year}-{datetime.strftime(updatedAt, '%m-%d %H:%M:%S')}"
            mayor_data = parse_cec_mayor(jsonfile["TC"])
            council_data = parse_cec_council(jsonfile["T1"] + jsonfile["T2"] + jsonfile["T3"])
            # Generate data for mayor and council members
            if IS_TV: 
                # Generate data for TV mayor
                try:
                    sht_data, source = parse_tv_sht()
                    gen_tv_mayor(updatedAt, source, sht_data, mayor_data, is_running=is_running)
                    print('tv mayor done')
                except googleapiclient.errors.HttpError:
                    print('sht failed')
            gen_mayor(updatedAt, mayor_data, is_running)
            print("Generated mayor data")
            gen_councilMember(updatedAt, council_data, is_running=is_running)
            print("Generated council member data")
        else:
            print('problem of get cec data ')
            if IS_TV:
                sht_data, source = parse_tv_sht()
                if 'cec' not in source.values():
                    gen_tv_mayor(source=source, sht_data=sht_data, is_running=True)
                    print('tv mayor done')
    else:# Generate default data if the election has not started and tks = 0
        if IS_TV:
            gen_tv_mayor()
            print("Generated TV mayor data")
        gen_councilMember()
        print("Generated council member data")
        gen_mayor()
        print("Generated mayor data")
    # Upload generated data
    upload_multiple_folders(year)
    return 'Done'


@app.route("/dump_politics", methods=['GET'])
def dump_election_politics():
    election_id = request.args.get('election_id', type=int)
    if election_id is None or election_id < 0:
        return "wrong election id"
    dump_politics(election_id)
    return "done"


@app.route("/landing_data", methods=['GET'])
def dump_landing():
    landing()
    return "done"


@app.route("/")
def healthcheck():
    return "ok"


if __name__ == "__main__":
    app.run()
