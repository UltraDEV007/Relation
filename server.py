from flask import Flask, request
from politics_dump import dump_politics, landing
import os
import googleapiclient
from datetime import datetime
from tools.cec_data import request_cec_by_type
from tools.uploadGCS import upload_multiple_folders
from referendum import parse_cec_referendum, gen_referendum
from mayor import gen_mayor, parse_cec_mayor, parse_tv_sht, gen_tv_mayor
from councilMember import gen_councilMember, parse_cec_council
app = Flask(__name__)

IS_TV =  os.environ['PROJECT'] == 'tv' 
IS_STARTED = os.environ['IS_STARTED'] == 'true'


@app.route("/elections_json_rf", methods=['GET'])
def elections_rf():
    if IS_STARTED:
        referendumfile, is_running = request_cec_by_type('rf')
        if referendumfile:
            polling_data = parse_cec_referendum(referendumfile)
            updatedAt = datetime.strptime(referendumfile["ST"], '%m%d%H%M%S')
            updatedAt = f"{datetime.now().year}-{datetime.strftime(updatedAt, '%m-%d %H:%M:%S')}"
            gen_referendum(updatedAt, polling_data, is_running=is_running)
            print("referendum done")
        else:
            print('problem of cec referendum data ')
    else:
        gen_referendum()
        print("referendum done")
    upload_multiple_folders()
    return 'done'


@app.route("/gen_elections_json", methods=['GET'])
def elections():
    if IS_STARTED:
        jsonfile, is_running = request_cec_by_type()
        if jsonfile:
            updatedAt = datetime.strptime(jsonfile["ST"], '%m%d%H%M%S')
            updatedAt = f"{datetime.now().year}-{datetime.strftime(updatedAt, '%m-%d %H:%M:%S')}"
            mayor_data = parse_cec_mayor(jsonfile["TC"])
            council_data = parse_cec_council(jsonfile["T1"] + jsonfile["T2"] + jsonfile["T3"])
            if IS_TV:
                try:
                    sht_data, source = parse_tv_sht()
                    gen_tv_mayor(updatedAt, source, sht_data, mayor_data)
                    print('tv mayor done')
                except googleapiclient.errors.HttpError:
                    print('sht failed')
            gen_mayor(updatedAt, mayor_data, is_running)
            print("mayor done")
            gen_councilMember(updatedAt, council_data, is_running)
            print("councilMember done")
        else:
            print('problem of cec data ')
            if IS_TV:
                sht_data, source = parse_tv_sht()
                if 'cec' not in source.values():
                    gen_tv_mayor(source=source, sht_data=sht_data)
                    print('tv mayor done')
    else:
        if IS_TV:
            gen_tv_mayor()
        gen_councilMember()
        print("councilMember done")
        gen_mayor()
        print("mayor done")
    upload_multiple_folders()
    return 'done'


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
