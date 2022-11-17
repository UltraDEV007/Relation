from flask import Flask, request
from politics_dump import dump_politics, landing
import os
import googleapiclient
from datetime import datetime
from tools.cec_data import request_cec_by_type
from referendum import parse_cec_referendum, gen_referendum
from mayor import gen_mayor, parse_cec_mayor, parse_tv_sht, gen_tv_mayor
from councilMember import gen_councilMember, parse_cec_council
app = Flask(__name__)

@app.route("/elections_json_rf", methods=['GET'])
def elections_rf():
    if os.environ['isSTARTED'] == 'true':
        referendumfile, is_running = request_cec_by_type('rf')
        if referendumfile:
            polling_data = parse_cec_referendum(referendumfile)
            updatedAt = referendumfile["ST"] 
            updatedAt = f"{datetime.now().year}-{updatedAt[:2]}-{updatedAt[2:4]} {updatedAt[4:6]}:{updatedAt[6:8]}:{updatedAt[8:10]}"# ‘0727172530’
            gen_referendum(updatedAt,polling_data, is_running=is_running)
            print("referendum done")
        else:
            print('problem of cec referendum data ')
    else:
        gen_referendum()
        print("referendum done")
    return 'done'

        

@app.route("/gen_elections_json", methods=['GET'])
def elections():
    if os.environ['isSTARTED'] == 'true':
        jsonfile, is_running = request_cec_by_type()
        if jsonfile is False:
            print('problem of cec data ')
            sht_data, source = parse_tv_sht()
            if 'cec' not in source.values():
                gen_tv_mayor(source=source, sht_data=sht_data)
                print('tv mayor done')
            
        else:
            polling_data = parse_cec_mayor(jsonfile["TC"])
            updatedAt = jsonfile["ST"] 
            updatedAt = f"{datetime.now().year}-{updatedAt[:2]}-{updatedAt[2:4]} {updatedAt[4:6]}:{updatedAt[6:8]}:{updatedAt[8:10]}"# ‘0727172530’
            try:
                sht_data, source = parse_tv_sht()
                gen_tv_mayor(updatedAt, source, sht_data, polling_data)
                print('tv mayor done')
            except googleapiclient.errors.HttpError:
                print('sht failed')
            gen_mayor(updatedAt, polling_data, is_running)
            print("mayor done")
            council_data = parse_cec_council(jsonfile["T1"] + jsonfile["T2"] + jsonfile["T3"])
            gen_councilMember(updatedAt, council_data, is_running)
            print("councilMember done")
            
    else:
        gen_tv_mayor()
        gen_mayor()
        print("mayor done")
        gen_councilMember()
        print("councilMember done")
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