from flask import Flask
from politics_candidate import generate_politic_candidate
from politics_dump import dump_politics

app = Flask(__name__)


@app.route("/candidate", methods=['GET'])
def process_data():
    generate_politic_candidate()
    return 'done'

@app.route("/dump_politics", method=['GET'])
def dump_election_politics():
    election_id = request.args.get('election_id', type = int)
    if election_id is None or election_id < 0:
        return "wrong election id"
    dump_politics(election_id)
    return "done"

@app.route("/")
def healthcheck():
    return "ok"


if __name__ == "__main__":
    app.run()
