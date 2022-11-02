from flask import Flask, request
from politics_candidate import generate_politic_candidate
from politics_dump import dump_politics, landing
from special_municipality import gen_special_municipality_polling

app = Flask(__name__)


@app.route("/candidate", methods=['GET'])
def process_data():
    generate_politic_candidate()
    return 'done'

@app.route("/dump_politics", methods=['GET'])
def dump_election_politics():
    election_id = request.args.get('election_id', type = int)
    if election_id is None or election_id < 0:
        return "wrong election id"
    dump_politics(election_id)
    return "done"

@app.route("/landing_data", methods=['GET'])
def dump_landing():
    landing()
    return "done"

@app.route("/special_municipality", methods=['GET'])
def municipality():
        gen_special_municipality_polling()
        return 'done'

# @app.route("/election_module", methods=['GET'])
# def election():
#       return 'done'
 
@app.route("/")
def healthcheck():
    return "ok"


if __name__ == "__main__":
    app.run()
