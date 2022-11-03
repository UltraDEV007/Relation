from flask import Flask, request
from politics_dump import dump_politics, landing
import os
from tools.cec_data import request_cec
from mayor import gen_mayor_by_cec, parse_cec_mayor

app = Flask(__name__)


@app.route("/gen_elections_json", methods=['GET'])
def elections():
    if os.environ['isSTARTED'] == 'true':
        jsonfile = request_cec()
        if jsonfile:
            polling_data = parse_cec_mayor(jsonfile["TC"])
            gen_mayor_by_cec(polling_data)
            print("mayor done")
            return 'done'
        return 'problem of cec data '
    else:
        gen_mayor_by_cec()
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
