import psycopg2
import psycopg2.extras
import os
import re
import csv
import json
from tools.uploadGCS import upload_blob

def dump_politics(election_id):
    db = os.environ['DATABASE']
    db_user = os.environ['DATABASE_USER']
    db_pw = os.environ['DATABASE_PASSWORD']
    db_host = os.environ['DATABASE_HOST']
    db_port = os.environ['DATABASE_PORT']
    election_area = {}

    keepalive_kwargs = {
        "keepalives": 1,
        "keepalives_idle": 60,
        "keepalives_interval": 10,
        "keepalives_count": 5
    }
    connection = psycopg2.connect(database=db, user=db_user,password=db_pw, host=db_host, port=db_port, **keepalive_kwargs)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    #dump_query = """SELECT "Politic"."id", "desc", "content", "Person"."name", "Election"."name", "ElectionArea"."name", "Organization"."name", "Tag"."name" FROM "Politic", "PersonElection", "Person", "Election", "ElectionArea", "Organization", "Tag" WHERE "Politic".person = "PersonElection".id AND "PersonElection".election = "Election"."id" AND "PersonElection"."person_id" = "Person"."id" AND "ElectionArea"."id" = "PersonElection"."electoral_district" AND ("Organization"."id" = "PersonElection"."party" OR "PersonElection"."party" is NULL) AND "Politic"."status" = 'verified' AND "Politic"."tag" = "Tag"."id" AND "Election".id = """ + str(election_id)
    dump_query = """SELECT "Politic"."id", "desc", "content", "Person"."name", "Election"."name", "ElectionArea"."name", "Tag"."name" FROM "Politic", "PersonElection", "Person", "Election", "ElectionArea", "Tag" WHERE "Politic".person = "PersonElection".id AND "PersonElection".election = "Election"."id" AND "PersonElection"."person_id" = "Person"."id" AND "ElectionArea"."id" = "PersonElection"."electoral_district" AND "Politic"."status" = 'verified' AND "Politic"."tag" = "Tag"."id" AND "Election".id = """ + str(election_id)
    cursor.execute(dump_query)
    all_politics = cursor.fetchall()
    destination_file = 'politics/politics-' + str(election_id) + ".csv"
    if not os.path.exists(os.path.dirname(destination_file)):
        os.makedirs(os.path.dirname(destination_file))

    with open(destination_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['政見 id', '政見', '政見補充', '候選人', '選舉', '選區', '政黨', '分類'])
        writer.writerows(all_politics)
        upload_blob(destination_file, 2022)
    connection.close()

def landing():
    db = os.environ['DATABASE']
    db_user = os.environ['DATABASE_USER']
    db_pw = os.environ['DATABASE_PASSWORD']
    db_host = os.environ['DATABASE_HOST']
    db_port = os.environ['DATABASE_PORT']
    election_config = os.environ['ELECTION_CONFIG']
    dest_file = os.environ['LANDING_DEST']
    result = {}

    keepalive_kwargs = {
        "keepalives": 1,
        "keepalives_idle": 60,
        "keepalives_interval": 10,
        "keepalives_count": 5
    }

    election_id = json.loads(election_config)
    connection = psycopg2.connect(database=db, user=db_user,password=db_pw, host=db_host, port=db_port, **keepalive_kwargs)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    for election in election_id:
        if isinstance(election["id"], list):
            multiple_election = True
        else:
            multiple_election = False 

        get_election_areas = """SELECT "ElectionArea"."id", "ElectionArea"."name", substring("ElectionArea"."name", 0, 4), substring("ElectionArea"."name", 5, 2) FROM "ElectionArea"  WHERE "ElectionArea"."election" = {};""".format(str(election["id"]))
        if multiple_election == True and len(election["id"]) == 2:
            get_election_areas = """SELECT "ElectionArea"."id", "ElectionArea"."name", substring("ElectionArea"."name", 0, 4), substring("ElectionArea"."name", 5, 2) FROM "ElectionArea"  WHERE "ElectionArea"."election" = {} OR "ElectionArea"."election" = {};""".format(str(election["id"][0]), str(election["id"][1]))
        cursor.execute(get_election_areas)
        election_areas = cursor.fetchall()
        area_hash = {}
        for area in election_areas:
            if area[2] not in area_hash:
                area_hash[area[2]] = []
            if area[3] and int(area[3]) > 0:
                order = int(area[3])
            else: 
                order = 0
            area_hash[area[2]].append({ "id": area[0], "order": order, "name": area[1], "city": area[2], "candidates": [] })
                
        #fetch politics
        dump_query = """SELECT count(person), "PersonElection"."person_id", "ElectionArea"."name"  FROM "Politic", "PersonElection", "ElectionArea" WHERE "ElectionArea"."id" = "PersonElection"."electoral_district" AND "Politic"."person" = "PersonElection"."id" AND "Politic"."status" = 'verified' AND "PersonElection"."election" = {} GROUP BY "PersonElection"."person_id", "ElectionArea"."name";""".format(str(election["id"]))
        if multiple_election == True and len(election["id"]) == 2:
            dump_query = """SELECT count(person), "PersonElection"."person_id", "ElectionArea"."name"  FROM "Politic", "PersonElection", "ElectionArea" WHERE "ElectionArea"."id" = "PersonElection"."electoral_district" AND "Politic"."person" = "PersonElection"."id" AND "Politic"."status" = 'verified' AND ("PersonElection"."election" = {} OR "PersonElection"."election" = {}) GROUP BY "PersonElection"."person_id", "ElectionArea"."name";""".format(str(election["id"][0]), str(election["id"][1]))
        cursor.execute(dump_query)
        all_politics = cursor.fetchall()
        dist_politic = {}
        dist_amount = {}
        for count in all_politics:
            dist_politic[count[1]] = count[0]
            if count[2] in dist_amount:
                dist_amount[count[2]] = dist_amount[count[2]] + 1
            else:
                dist_amount[count[2]] = 1
        result[election["total"]] = len(dist_politic)
        #fetch all candidates
        get_candidates = """SELECT "Person"."birth_date_year", "PersonElection"."person_id", "Person"."name", "ElectionArea"."name" FROM "Person", "Election", "PersonElection", "ElectionArea" WHERE "Election".id = {} AND "ElectionArea"."id" = "PersonElection"."electoral_district" AND "PersonElection"."election" = "Election"."id" AND "Person".id = "PersonElection"."person_id";""".format(str(election["id"]))
        if multiple_election == True and len(election["id"]) == 2:
            get_candidates = """SELECT "Person"."birth_date_year", "PersonElection"."person_id", "Person"."name", "ElectionArea"."name" FROM "Person", "Election", "PersonElection", "ElectionArea" WHERE ("Election".id = {} OR "Election".id = {}) AND "ElectionArea"."id" = "PersonElection"."electoral_district" AND "PersonElection"."election" = "Election"."id" AND "Person".id = "PersonElection"."person_id";""".format(str(election["id"][0]), str(election["id"][1]))
        cursor.execute(get_candidates)
        all_candidates = cursor.fetchall()
        area_candidates = {}
        for candidate in all_candidates:
            if candidate[1] in dist_politic:
                done = dist_politic[candidate[1]]
            else:
                done = 0
            if candidate[3] not in area_candidates:
                area_candidates[candidate[3]] = []

            area_candidates[candidate[3]].append( { "id": candidate[1], "name": candidate[2], "year": candidate[0], "done": done } )

        # parse data    
        if election['type'] == 'mayorAndPolitics':
            result['mayorAndPolitics'] = []
            result['mayorAndPolitics'].append( {"key": "north", "name": "北部", "amount": 5, "total": 40, "areas": [ 
                {"name": "宜蘭縣", "city": "宜蘭縣", "total": 6 }, 
                {"name": "新竹縣", "city": "新竹縣", "total": 5 },
                {"name": "新竹市", "city": "新竹市", "total": 6 },
                {"name": "桃園市", "city": "桃園市", "total": 4 },
                {"name": "臺北市", "city": "臺北市", "total": 12 },
                {"name": "新北市", "city": "新北市", "total": 2 },
                {"name": "基隆市", "city": "基隆市", "total": 5 },
            ] } )
            result['mayorAndPolitics'].append( {"key": "center", "name": "中部", "amount": 0, "total": 17, "areas": [
                {"name": "苗栗縣", "city": "苗栗縣", "total": 0 },
                {"name": "彰化縣", "city": "彰化縣", "total": 0 },
                {"name": "雲林縣", "city": "雲林縣", "total": 0 },
                {"name": "南投縣", "city": "南投縣", "total": 0 },
                {"name": "臺中市", "city": "臺中市", "total": 0 },
            ]} )
            result['mayorAndPolitics'].append( {"key": "south", "name": "南部", "amount": 0, "total": 17, "areas": [
                {"name": "臺南市", "city": "臺南市", "total": 0 },
                {"name": "屏東縣", "city": "屏東縣", "total": 0 },
                {"name": "嘉義縣", "city": "嘉義縣", "total": 0 },
                {"name": "高雄市", "city": "高雄市", "total": 0 },
                {"name": "嘉義市", "city": "嘉義市", "total": 0 },
            ]} )
            result['mayorAndPolitics'].append( {"key": "east", "name": "東部", "amount": 0, "total": 6, "areas": [
                {"name": "花蓮縣", "city": "花蓮縣", "total": 0 },
                {"name": "臺東縣", "city": "臺東縣", "total": 0 },
            ]} )
            result['mayorAndPolitics'].append( {"key": "island", "name": "離島", "amount": 0, "total": 12, "areas": [
                {"name": "金門縣", "city": "金門縣", "total": 0 },
                {"name": "澎湖縣", "city": "澎湖縣", "total": 0 },
                {"name": "連江縣", "city": "連江縣", "total": 0 },
            ]} )
            for section in result['mayorAndPolitics']:
                section_amount = 0
                section_total = 0
                for section_area in section['areas']:
                    section_area_amount = 0
                    if section_area['name'] in area_hash:
                        section_area['id'] = area_hash[section_area['name']][0]["id"]
                    if section_area['name'] in area_candidates:
                        if section_area['name'] in dist_amount:
                            section_area["done"] = dist_amount[section_area["name"]]
                            section_amount = section_amount + dist_amount[section_area["name"]]
                        else:
                            section_area["done"] = 0
                        section_area["candidates"] = area_candidates[section_area['name']]
                        section_area["total"] = len(area_candidates[section_area['name']])
                        section_total = section_total + section_area["total"]
                        section_area_amount = section_area_amount = section_area["total"]
                section['amount'] = section_amount
                section['total'] = section_total
                    
        elif election['type'] == 'councilorAndPolitics' or election['type'] == 'regionalLegislator':
            result[election['type']] = []
            result[election['type']].append( {"name": "基隆市", "amount": 0, "total": 0, "areas": []} )
            result[election['type']].append( {"name": "高雄市", "amount": 0, "total": 0, "areas": []} )
            result[election['type']].append( {"name": "嘉義市", "amount": 0, "total": 0, "areas": []} )
            result[election['type']].append( {"name": "金門縣", "amount": 0, "total": 0, "areas": []} )
            result[election['type']].append( {"name": "屏東縣", "amount": 0, "total": 0, "areas": []} )
            result[election['type']].append( {"name": "宜蘭縣", "amount": 0, "total": 0, "areas": []} )
            result[election['type']].append( {"name": "桃園市", "amount": 0, "total": 0, "areas": []} )
            result[election['type']].append( {"name": "苗栗縣", "amount": 0, "total": 0, "areas": []} )
            result[election['type']].append( {"name": "臺中市", "amount": 0, "total": 0, "areas": []} )
            result[election['type']].append( {"name": "新竹市", "amount": 0, "total": 0, "areas": []} )
            result[election['type']].append( {"name": "嘉義縣", "amount": 0, "total": 0, "areas": []} )
            result[election['type']].append( {"name": "澎湖縣", "amount": 0, "total": 0, "areas": []} )
            result[election['type']].append( {"name": "彰化縣", "amount": 0, "total": 0, "areas": []} )
            result[election['type']].append( {"name": "臺南市", "amount": 0, "total": 0, "areas": []} )
            result[election['type']].append( {"name": "臺北市", "amount": 0, "total": 0, "areas": []} )
            result[election['type']].append( {"name": "連江縣", "amount": 0, "total": 0, "areas": []} )
            result[election['type']].append( {"name": "新竹縣", "amount": 0, "total": 0, "areas": []} )
            result[election['type']].append( {"name": "雲林縣", "amount": 0, "total": 0, "areas": []} )
            result[election['type']].append( {"name": "新北市", "amount": 0, "total": 0, "areas": []} )
            result[election['type']].append( {"name": "花蓮縣", "amount": 0, "total": 0, "areas": []} )
            result[election['type']].append( {"name": "南投縣", "amount": 0, "total": 0, "areas": []} )
            result[election['type']].append( {"name": "臺東縣", "amount": 0, "total": 0, "areas": []} )
            for councilor in result[election['type']]:
                councilor_amount = 0
                councilor_total = 0
                if councilor["name"] in area_hash:
                    councilor["areas"] = area_hash[councilor["name"]]
                    for area in councilor["areas"]:
                        area_amount = 0
                        if area['name'] in area_candidates:
                            area["candidates"] = area_candidates[area['name']]
                            area["total"] = len(area_candidates[area['name']])
                            councilor_total = councilor_total + area["total"]
                            for candidate in area['candidates']:
                                if candidate['done'] > 0:
                                    area_amount = area_amount + 1
                        area['done'] = area_amount
                        councilor_amount = councilor_amount + area_amount
                    councilor['amount'] = councilor_amount
                    councilor['total'] = councilor_total
        elif election['type'] == 'aboriginalLegislator' or election['type'] == 'flatAboriginalLegislator':
            result[election['type']] = []
            result[election['type']].append( {"name": "全國", "amount": 0, "total": 0, "areas": []} )
            for councilor in result[election['type']]:
                councilor_amount = 0
                councilor_total = 0
                if councilor["name"] in area_hash:
                    councilor["areas"] = area_hash[councilor["name"]]
                    for area in councilor["areas"]:
                        area_amount = 0
                        if area['name'] in area_candidates:
                            area["candidates"] = area_candidates[area['name']]
                            area["total"] = len(area_candidates[area['name']])
                            councilor_total = councilor_total + area["total"]
                            for candidate in area['candidates']:
                                if candidate['done'] > 0:
                                    area_amount = area_amount + 1
                        area['done'] = area_amount
                        councilor_amount = councilor_amount + area_amount
                    councilor['amount'] = councilor_amount
                    councilor['total'] = councilor_total
        elif election['type'] == 'nonRegionalLegislator':
            #fetch politics
            dump_query = """SELECT count("Politic"."id"), "Organization"."name", "OrganizationsElection"."organization_id" FROM "Politic", "OrganizationsElection", "Organization" WHERE "Politic"."organization" = "Organization"."id" AND "Organization"."id" = "OrganizationsElection"."organization_id" AND "OrganizationsElection"."elections" = {} GROUP BY "OrganizationsElection"."organization_id", "Organization"."name";""".format(str(election["id"]))
            cursor.execute(dump_query)
            all_politics = cursor.fetchall()
            dist_politic = {}
            dist_amount = { '全國': 0 }
            for count in all_politics:
                dist_politic[count[1]] = count[0]
                dist_amount['全國'] = dist_amount['全國'] + 1
            result[election["total"]] = len(dist_politic)
            #fetch all candidates
            get_candidates = """SELECT "Organization"."name", "OrganizationsElection"."organization_id", '全國' as area FROM "OrganizationsElection", "Organization" WHERE "Organization"."id" = "OrganizationsElection"."organization_id" AND "OrganizationsElection"."elections" = {}""".format(str(election["id"]))
            cursor.execute(get_candidates)
            all_candidates = cursor.fetchall()
            area_candidates = {}
            for candidate in all_candidates:
                if candidate[0] in dist_politic:
                    done = dist_politic[candidate[0]]
                else:
                    done = 0
                if candidate[2] not in area_candidates:
                    area_candidates[candidate[2]] = []

                area_candidates[candidate[2]].append( { "id": candidate[1], "name": candidate[0], "done": done } )

        # parse data    
            result[election['type']] = []
            result[election['type']].append( {"name": "全國", "amount": 0, "total": 0, "areas": []} )
            for councilor in result[election['type']]:
                councilor_amount = 0
                councilor_total = 0
                if councilor["name"] in area_hash:
                    councilor["areas"] = area_hash[councilor["name"]]
                    for area in councilor["areas"]:
                        area_amount = 0
                        if area['name'] in area_candidates:
                            area["candidates"] = area_candidates[area['name']]
                            area["total"] = len(area_candidates[area['name']])
                            councilor_total = councilor_total + area["total"]
                            for candidate in area['candidates']:
                                if candidate['done'] > 0:
                                    area_amount = area_amount + 1
                        area['done'] = area_amount
                        councilor_amount = councilor_amount + area_amount
                    councilor['amount'] = councilor_amount
                    councilor['total'] = councilor_total
        # parse candidates
        if not os.path.exists(os.path.dirname(dest_file)):
            os.makedirs(os.path.dirname(dest_file))

        with open(dest_file, 'w', encoding='utf8') as json_file:
            result_json = json.dumps(result, ensure_ascii=False)
            json_file.write(result_json)
        
        upload_blob(dest_file, 2024)
    connection.close()




if __name__=="__main__":
    landing()
