from flask import Flask
from politics_candidate import generate_politic_candidate

app = Flask(__name__)


@app.route("/candidate", methods=['GET'])
def process_data():
    generate_politic_candidate()
    return 'done'


@app.route("/")
def healthcheck():
    return "ok"


if __name__ == "__main__":
    app.run()
