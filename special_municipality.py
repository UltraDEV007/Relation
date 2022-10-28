from datetime import datetime
import json
import os
from gql import gql
from configs import special_municipality, default_special_municipality
from tools.uploadGCS import upload_blob
from tools.conn import gql_client
from tools.cec_data import request_cec


def get_personElection_from_cms(electoral_district):
    county = {}
    query = '''
     query{
    personElections(where:{
        election:{id:{equals:81}},
        electoral_district:{name:{contains:"%s"}},
    }){
    number
    party{
      name
    }
        person_id{
          name
        }
    
    }
    }''' % electoral_district
    client = gql_client()
    r = client.execute(gql(query))
    if r['personElections']:
        for candidate in r['personElections']:
            candNo = int(candidate['number'])
            county[candNo] = {}
            county[candNo]["name"] = candidate['person_id']['name']
            county[candNo]["party"] = candidate['party']['name'] if candidate['party'] else "無"
    return county


def parse_default():
    for special_municipality in default_special_municipality:
        city = special_municipality['city']
        mapping_candNo = get_personElection_from_cms(city)
        candidates = []
        print(city)
        for candNo in special_municipality['candidates']:
            candTks = {
                "candNo": str(candNo).zfill(2),
                "name": mapping_candNo[candNo]['name'],
                "party": mapping_candNo[candNo]['party'],
                "tks": 0,
                "tksRate": 0,
                "candVictor": False,
            }
            candidates.append(candTks)
        special_municipality["candidates"] = candidates
    return default_special_municipality


def parse_cec_data():
    jsonfile = request_cec()
    if jsonfile:
        jsonfile = jsonfile["TC"]
        with open('election-polling/mapping/mapping_county_district.json') as f:
            mapping_city = json.loads(f.read())

        for data in jsonfile:
            # 直轄市
            if data["prvCode"] and data["cityCode"] == "000" and data["areaCode"] is None and data["deptCode"] is None:
                city_code = f'{data["prvCode"]}_{data["cityCode"]}_000'
                city = mapping_city[city_code]
                print(city)
                mapping_candNo = get_personElection_from_cms(city)
                candidates = []
                for candTksInfo in data["candTksInfo"]:
                    # print(candTksInfo)
                    candTks = {}
                    if candTksInfo["candNo"]:
                        candTks["candNo"] = str(candTksInfo["candNo"]).zfill(2)
                    else:
                        print(" cec data candNo is null.")
                        return
                    try:
                        candTks["name"] = mapping_candNo[candTksInfo["candNo"]]['name']
                    except KeyError:
                        candTks["name"] = ''
                    try:
                        candTks["party"] = mapping_candNo[candTksInfo["candNo"]]['party']
                    except KeyError:
                        candTks["party"] = ''
                    if candTksInfo["tks"] is not None:
                        candTks["tks"] = int(candTksInfo["tks"])
                    else:
                        print(" cec data tks is null.")
                        return
                    if candTksInfo["tksRate"] is not None:
                        candTks["tksRate"] = float(candTksInfo["tksRate"])
                    else:
                        print(" cec data tksRate is null.")
                        return
                    candTks["candVictor"] = True if candTksInfo["candVictor"] == "*" else False
                    candidates.append(candTks)
                # first sort by tks desc, if same tks sort by candNo asc
                candidates.sort(
                    key=lambda x: (-x["tks"], x["candNo"]), reverse=False)
                # sort county by config order
                special_municipality[city] = {
                    "city": city, "candidates": candidates[:3]}

        return [v for v in special_municipality.values()]
    return False


def gen_special_municipality_polling():
    if os.environ['isSTARTED'] == 'true':
        result = parse_cec_data()
        if result is False:
            return
    else:
        result = parse_default()
    destination_file = 'elections/real-time/election2022.json'
    if not os.path.exists(os.path.dirname(destination_file)):
        os.makedirs(os.path.dirname(destination_file))
    with open(destination_file, 'w') as f:
        f.write(json.dumps({"updatedAt": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "polling": result}, ensure_ascii=False))
    upload_blob(destination_file, year=2022)


if __name__ == '__main__':
    gen_special_municipality_polling()
