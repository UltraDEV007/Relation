import os
import googleapiclient
from flask import Flask, request
from politics_dump import dump_politics, landing
from datetime import datetime
from tools.cec_data import request_cec_by_type, request_cec
from tools.uploadGCS import upload_multiple_folders
from referendum import parse_cec_referendum, gen_referendum
from mayor import gen_mayor, parse_cec_mayor, parse_tv_sht, gen_tv_mayor
from councilMember import gen_councilMember, parse_cec_council
from election import factcheck_data, election2024, politics_dump
from data_export import president2024_realtime

from data_handlers import pipeline

app = Flask(__name__)

IS_TV =  os.environ['PROJECT'] == 'tv' 
IS_STARTED = os.environ['IS_STARTED'] == 'true'

### new version implementations
@app.route('/elections/presidents/2024', methods=['POST'])
def president_2024():
    '''
        Generate result for presidents and vice presidents election
    '''
    # if IS_STARTED:
    #     raw_data, is_running = request_cec_by_type()
    #     if raw_data:
    #         # TODO: Parse election_data and store
    #         preprocessing_data = preprocessor.parse_president_cec(raw_data)
    if IS_STARTED:
        raw_data = request_cec('final.json')
        if raw_data:
            result = pipeline.pipeline_2024(raw_data, is_started = IS_STARTED, is_running = False)
            if result == False:
                print('Running pipeline 2024 failed.')
            else:
                print('Running pipeline 2024 successed.')
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
