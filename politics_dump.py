import psycopg2
import psycopg2.extras
import os
import csv
from tools.uploadGCS import upload_blob

def dump_politics(election_id):
    db = os.environ['DATABASE']
    db_user = os.environ['DATABASE_USER']
    db_pw = os.environ['DATABASE_PASSWORD']
    db_host = os.environ['DATABASE_HOST']
    db_port = os.environ['DATABASE_PORT']

    keepalive_kwargs = {
        "keepalives": 1,
        "keepalives_idle": 60,
        "keepalives_interval": 10,
        "keepalives_count": 5
    }
    connection = psycopg2.connect(database=db, user=db_user,password=db_pw, host=db_host, port=db_port, **keepalive_kwargs)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    dump_query = """SELECT "desc", "content", "Person"."name", "Election"."name", "ElectionArea"."name", "Organization"."name" FROM "Politic", "PersonElection", "Person", "Election", "ElectionArea", "Organization" WHERE "Politic".person = "PersonElection".id AND "PersonElection".election = "Election"."id" AND "PersonElection"."person_id" = "Person"."id" AND "ElectionArea"."id" = "PersonElection"."electoral_district" AND "Organization"."id" = "PersonElection"."party" AND "Politic"."status" = 'verified' AND "Election".id = """ + str(election_id)
    cursor.execute(dump_query)
    all_politics = cursor.fetchall()
    destination_file = 'politics/politics-' + str(election_id) + ".csv"
    if not os.path.exists(os.path.dirname(destination_file)):
        os.makedirs(os.path.dirname(destination_file))

    with open(destination_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['政見', '政見補充', '候選人', '選舉', '選區', '政黨'])
        writer.writerows(all_politics)
        upload_blob(destination_file, 2022)

    connection.close()

if __name__=="__main__":
    dump_politics(82)
