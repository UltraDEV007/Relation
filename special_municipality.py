from datetime import datetime
import json
import os
from gql import gql
from configs import special_municipality, default_special_municipality
from tools.uploadGCS import upload_blob
from tools.cec_data import request_cec


def parse_default(candidate_info):
    default = []
    for city_name, defl_candNo  in default_special_municipality.items():
        mapping_candNo = candidate_info[city_name]
        candidates = []
        print(city_name)
        for candNo in defl_candNo:
            candTks = {
                "candNo": str(candNo).zfill(2),
                "name": mapping_candNo[str(candNo)]['name'],
                "party": mapping_candNo[str(candNo)]['party'],
                "tks": 0,
                "tksRate": 0,
                "candVictor": False,
            }
            candidates.append(candTks)
        default.append({"city": city_name, "candidates": candidates})
    return default


def parse_cec_data(candidate_info):
    jsonfile = request_cec()
    if jsonfile:
        jsonfile = jsonfile["TC"]
        with open('mapping/mapping_county_district.json') as f:
            mapping_city = json.loads(f.read())

        for data in jsonfile:
            # 直轄市
            if data["prvCode"] and data["cityCode"] == "000" and data["areaCode"] is None and data["deptCode"] is None:
                city_code = f'{data["prvCode"]}_{data["cityCode"]}_000'
                city = mapping_city[city_code]
                print(city)
                mapping_candNo = candidate_info[city]
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
                        candTks["name"] = mapping_candNo[str(candTksInfo["candNo"])]['name']
                    except KeyError:
                        candTks["name"] = ''
                    try:
                        candTks["party"] = mapping_candNo[str(candTksInfo["candNo"])]['party']
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
    with open('mapping/mayor_candidate.json') as f:
        candidate_info = json.loads(f.read())
    if os.environ['isSTARTED'] == 'true':
        result = parse_cec_data(candidate_info)
        if result is False:
            return
    else:
        result = parse_default(candidate_info)

    year = datetime.now().year
    ELECTION_TYPE = os.environ['ELECTION_TYPE']
    destination_file = f'elections/{year}/{ELECTION_TYPE}/special_municipality.json'
    if not os.path.exists(os.path.dirname(destination_file)):
        os.makedirs(os.path.dirname(destination_file))
    with open(destination_file, 'w') as f:
        f.write(json.dumps({"updatedAt": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "polling": result}, ensure_ascii=False))
    upload_blob(destination_file, year)


if __name__ == '__main__':
    gen_special_municipality_polling()
