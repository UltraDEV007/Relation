import os
import googleapiclient
from flask import Flask, request
from politics_dump import dump_politics, landing
from datetime import datetime
from tools.cec_data import request_cec_by_type, request_cec, check_existed_cec_file
from tools.uploadGCS import upload_multiple_folders, upload_multiple
from referendum import parse_cec_referendum, gen_referendum
from mayor import gen_mayor, parse_cec_mayor, parse_tv_sht, gen_tv_mayor
from councilMember import gen_councilMember, parse_cec_council
from election import factcheck_data, election2024, politics_dump
from data_export import president2024_realtime

import data_handlers.helpers as hp
import data_handlers.parser as parser

from data_handlers import pipeline
import time
import copy

app = Flask(__name__)

IS_TV =  os.environ['PROJECT'] == 'tv' 
IS_STARTED = os.environ['IS_STARTED'] == 'true'

### election 2024
@app.route('/elctions/all/2024', methods=['POST'])
def election_all_2024():
    '''
        Generate both map and v2 data in one batch
    '''
    if IS_STARTED:
        ### 當IS_STARTED開始時，我們重新產生DEFAULT的文件
        if hp.HAS_CREATE_DEFAULT==False:
            _ = pipeline.pipeline_default_map(is_started=IS_STARTED)
            _ = pipeline.pipeline_default_seats()
            upload_multiple('2024', upload_map=True, upload_v2=True)
            hp.HAS_CREATE_DEFAULT = True
        
        hp.mapping_party_seat = copy.deepcopy(hp.mapping_party_seat_init)
        prev_time = time.time()
        seats_data = request_cec('final_A.json')
        raw_data, is_running = request_cec_by_type()
        if seats_data:
            print('Receive final_A data, write the seats information')
            parser.parse_seat(seats_data, hp.mapping_party_seat)
        cur_time = time.time()
        print(f'Time of fetching CEC data is {round(cur_time-prev_time,2)}s, is_running={is_running}')

        prev_time = cur_time
        ### 當raw_data存在時，表示有取得新一筆的資料，處理完後需上傳(若無新資料就不處理)
        if raw_data:
            _ = pipeline.pipeline_map_2024(raw_data, is_started = IS_STARTED, is_running=is_running, upload=False)
            _ = pipeline.pipeline_v2(raw_data, seats_data, '2024', is_running=is_running, upload=False)
            _ = pipeline.pipeline_map_seats(raw_data)
            cur_time = time.time()
            print(f'Time of map&v2 pipeline is {round(cur_time-prev_time,2)}s')
            upload_multiple('2024', upload_map=True, upload_v2=True)
    else:
        _ = pipeline.pipeline_default_map(is_started=IS_STARTED)
        _ = pipeline.pipeline_default_seats()
        upload_multiple('2024', upload_map=True, upload_v2=True)
    return "ok"

@app.route('/elections/2024/default', methods=['POST'])
def election_all_default():
    '''
        Test API for creating default json files
    '''
    _ = pipeline.pipeline_default_map(is_started=IS_STARTED)
    _ = pipeline.pipeline_default_seats()
    upload_multiple('2024', upload_map=True, upload_v2=True)
    return "ok"

@app.route('/elections/cec/fetch', methods=['POST'])
def cec_fetch():
    '''
        Fetch CEC data only
    '''
    if IS_STARTED:
        hp.mapping_party_seat = copy.deepcopy(hp.mapping_party_seat_init)
        seats_data = request_cec('final_A.json')
        _, _ = request_cec_by_type()
        if seats_data:
            print('Receive final_A data, write the seats information')
            parser.parse_seat(seats_data, hp.mapping_party_seat)
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
