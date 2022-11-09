from datetime import datetime
import json
import os
from tools.uploadGCS import save_file
from tools.cec_data import request_cec
from tools.conn import get_sht_data
from configs import default_special_municipality, default_tv
import googleapiclient
with open('mapping/mapping_county_town.json') as f:
    mapping_county_town = json.loads(f.read())
with open('mapping/mapping_county_town_vill.json') as f:
    mapping_county_town_vill = json.loads(f.read())
with open('mapping/mayor_candidate_2022.json') as f:
    candidate_info = json.loads(f.read())
ENV_FOLDER = os.environ['ENV_FOLDER']


def parse_cec_mayor(data):
    organized_data = {}
    for district in data:
        deptCode = district['deptCode'] if district['deptCode'] else '000'
        region_code = f"{district['prvCode']}_{district['cityCode']}_{deptCode}"
        region = organized_data.setdefault(region_code, {'profRate': district['profRate']})
        for c in district['candTksInfo']:
            candNo = region.setdefault(c['candNo'], c)
            candNo = c
    return organized_data


def parse_tv_sht():
    sht_data = {}
    source = {}
    sht_data_raw = get_sht_data(url=os.environ['SHT_URL'], shtID=os.environ['WKS_ID'])
    for row in sht_data_raw:
        if row[0] == '城市名' or not row[0]:
            continue
        county_name = row[0].replace('台', '臺')
        candNo = int(row[2])
        name = row[1]
        party = row[3]
        tks = int(row[5].replace(',', ''))
        tksRate = float(row[4].replace('%', ''))
        candVictor = False
        county_source = source.setdefault(county_name, row[6])
        if county_source == '自行計票 + 候選人計票' or county_source == 'tv':
            county_source = 'tv'
        else:
            county_source = 'cec'
        source[county_name] = county_source
        # candidates
        county = sht_data.setdefault(county_name, {candNo: {}})
        county[candNo] = {
            "candNo": candNo,
            "name": name,
            "party": party,
            "tks": tks,
            "tksRate": tksRate,
            "candVictor": candVictor
        }
        #     candidateNo = row[2]
    return sht_data, source
def gen_tv_mayor(source='', sht_data='', polling_data=''):
    result = []
    if source:
        for county_name, candNos in sht_data.items():
            candidates = []
            if source[county_name] == 'tv':
                county_source = '自行計票 + 候選人計票'
                cand_infos = sht_data[county_name]
            else:
                county_source = '中選會'
                county_code = [k for k in mapping_county_town.keys()][[v for v in mapping_county_town.values()].index(county_name)]
                cand_infos = polling_data[county_code]
            for candNo in candNos.keys():
                try:
                    candidate = {
                        "candNo": str(candNo).zfill(2),
                        "name": sht_data[county_name][candNo]['name'],
                        "party": sht_data[county_name][candNo]['party'],
                        "tks": cand_infos[candNo]['tks'],
                        "tksRate": cand_infos[candNo]['tksRate'],
                        "candVictor": True if cand_infos[candNo]['candVictor'] == "*" else False
                        }
                except KeyError:
                    candidate = {
                        "candNo": str(candNo).zfill(2),
                        "name": sht_data[county_name][candNo]['name'],
                        "party": sht_data[county_name][candNo]['party'],
                        "tks": 0,
                        "tksRate": 0,
                        "candVictor": False
                        }

                candidates.append(candidate) 
            candidates.sort(key=lambda x: (-x["tks"], x["candNo"]), reverse=False)
            result.append(
                {"city": county_name, "candidates": candidates, "source" : county_source})
    else:
        for county_code, default_candidates in default_tv.items():
            candidates = []
            county_source = "中選會"
            county_name = mapping_county_town[county_code]
            for candNo in default_candidates:
                    c_info = candidate_info[county_code][str(candNo)]
                    candTks = {
                        "candNo": str(candNo).zfill(2),
                        "name": c_info['name'],
                        "party": c_info['party'],
                        "tks": 0,
                        "tksRate": 0,
                        "candVictor": False,
                    }
                    candidates.append(candTks)
            candidates.sort(key=lambda x: (-x["tks"], x["candNo"]), reverse=False)
            result.append(
                {"city": mapping_county_town[county_code], "candidates": candidates[:3], "source" : county_source})
    year = datetime.now().year
    destination_file = f'{ENV_FOLDER}/{year}/mayor/tv.json'
    data = {"updatedAt": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "polling": result}
    save_file(destination_file, data, year)
    return
    

def gen_special_municipality(polling_data):
    result = []
    for county_code, default_candidates in default_special_municipality.items():
        candidates = []
        if polling_data:
            for candNo, c_info in candidate_info[county_code].items():
                try:
                    tksRate = polling_data[county_code][int(
                        candNo)]['tksRate'] if polling_data[county_code][int(candNo)]['tksRate'] else 0
                    tks = polling_data[county_code][int(
                        candNo)]['tks'] if polling_data[county_code][int(candNo)]['tks'] else 0
                    candVictor = True if polling_data[county_code][int(candNo)]['candVictor'] == '*' else False
                except:
                    tksRate = 0
                    tks = 0
                    candVictor = False
                candTks = {
                    "candNo": candNo.zfill(2),
                    "name": c_info['name'],
                    "party": c_info['party'],
                    "tks": tks,
                    "tksRate": tksRate,
                    "candVictor":  candVictor,
                }
                candidates.append(candTks)
        else:
            for candNo in default_candidates:
                c_info = candidate_info[county_code][str(candNo)]
                candTks = {
                    "candNo": str(candNo).zfill(2),
                    "name": c_info['name'],
                    "party": c_info['party'],
                    "tks": 0,
                    "tksRate": 0,
                    "candVictor": False,
                }
                candidates.append(candTks)
        candidates.sort(key=lambda x: (-x["tks"], x["candNo"]), reverse=False)
        result.append(
            {"city": mapping_county_town[county_code], "candidates": candidates[:3]})
    year = datetime.now().year
    destination_file = f'{ENV_FOLDER}/{year}/mayor/special_municipality.json'
    data = {"updatedAt": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "polling": result}
    save_file(destination_file, data, year)
    return


def gen_vote(polling_data='', candidate_info=candidate_info, year=datetime.now().year):
    result = []
    for region_code, region_candidates in candidate_info.items():
        candidates = []
        for candNo, c_info in region_candidates.items():
            candTks = {
                'candNo': candNo,
                'name': {
                    'label': c_info['name'],
                    'href': f"./person/{c_info['name_id']}",
                    'imgSrc': c_info['name_img'] if c_info['name_img'] else ''
                },
                'party': {
                    'label': c_info['party'] if c_info['party'] != '無' else '無黨籍',
                    'href': '',
                    'imgSrc': c_info['party_img'] if c_info['party_img'] else ''
                },
                'tks': 0,
                'tksRate': 0,
                'candVictor': False
            }
            if polling_data:
                try:
                    candTks['tks'] = polling_data[region_code][int(
                        candNo)]['tks'] if polling_data[region_code][int(candNo)]['tks'] else 0
                    candTks['tksRate'] = polling_data[region_code][int(
                        candNo)]['tksRate'] if polling_data[region_code][int(candNo)]['tksRate'] else 0
                    candTks['candVictor'] = True if polling_data[region_code][int(
                        candNo)]['candVictor'] == '*' or polling_data[region_code][int(
                        candNo)]['candVictor'] == True else False
                except KeyError:
                    pass
            candidates.append(candTks)
        try:
            districtName = mapping_county_town[region_code]
        except KeyError:
            districtName = region_code

        result.append(
            {"districtName": districtName, "candidates": candidates})

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    VERSION = os.environ['VERSION']
    data = {"updatedAt": now,
            "year": str(year),
            "type": 'mayor',
            "title": "縣市長選舉",
            "version": VERSION,
            "districts": result}
    destination_file = f'{ENV_FOLDER}/{VERSION}/{year}/mayor/all.json'

    save_file(destination_file, data, year)
    return


def map_candidate(region_candidates, polling_data, region_code):
    candidates = []
    for candNo, c_info in region_candidates.items():

        candTks = {
            "candNo": candNo,
            "name": c_info['name'],
            "party": c_info['party'] if c_info['party'] != '無' else '無黨籍',
            "tksRate": 0,
            "candVictor": " "
        }
        if polling_data:
            try:
                can_polling_data = polling_data[region_code][int(candNo)]
                candTks['tks'] = can_polling_data['tks'] if can_polling_data['tks'] else 0
                candTks['tksRate'] = can_polling_data['tksRate'] if can_polling_data['tksRate'] else 0
                candTks['candVictor'] = can_polling_data['candVictor'] if can_polling_data['candVictor']else ' '
            except KeyError:
                pass
        candidates.append(candTks)

    return candidates


def gen_map(scope, polling_data,  scope_code='', sub_region=''):
    result = []
    for region_code in sub_region.keys():
        if scope == 'country':
            vill_Code = '000'
            range = mapping_county_town[region_code]
        elif scope == 'county':
            region_code = scope_code[:-3] + region_code  # county code '09_007_010'
            vill_Code = '000'
            range = f'{mapping_county_town[scope_code]} {mapping_county_town[region_code]}'
        else:
            vill_Code = region_code
            region_code = scope_code + '_' + region_code  # vill code '09_007_010_010'
            range = sub_region[vill_Code].replace("_", " ")

        region_code_split = region_code.split('_')
        county_code = region_code_split[0] + '_' + region_code_split[1]
        town_code = region_code_split[2]

        candidates = map_candidate(candidate_info[f"{county_code}_000"], polling_data, region_code)
        if polling_data:
            profRate = polling_data[region_code]['profRate'] if polling_data[region_code]['profRate'] else 0
        else:
            profRate = 0
            if scope == 'town':
                profRate = None
                candidates = None

        result.append({
            "range": range,
            "county": county_code.replace('_', ''),
            "town": None if town_code == '000' else town_code,
            "vill": None if vill_Code == '000' else vill_Code,
            "profRate": profRate,
            "candidates": candidates})
    year = datetime.now().year
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data = {"updatedAt": now,
            "districts": result}
    if scope == 'country':
        destination_file = f'{ENV_FOLDER}/{year}/mayor/map/{scope}.json'
    elif scope == 'county':
        destination_file = f'{ENV_FOLDER}/{year}/mayor/map/{scope}/{scope_code[:-3].replace("_", "")}.json'
    else:
        destination_file = f'{ENV_FOLDER}/{year}/mayor/map/{scope}/{scope_code.replace("_", "")}.json'

    save_file(destination_file, dict(sorted(data.items(), reverse=True)), year)
    return


def gen_mayor(data = ''):
    gen_special_municipality(data)
    gen_vote(data)
    gen_map('country', data, '00_000_000', candidate_info)
    for county_code, towns in mapping_county_town_vill.items():
        if county_code == '10_020':#2022嘉義市長選舉延後
            continue
        county_code = county_code + '_000'
        gen_map('county', data, county_code, towns)
        if os.environ['isSTARTED'] != 'true':
            for town_code, vills in towns.items():
                town_code = county_code[:-3] + town_code
                gen_map('town', polling_data='',
                        scope_code = town_code, sub_region=vills)
    return


if __name__ == '__main__':
    if os.environ['isSTARTED'] == 'true':
        jsonfile = request_cec('running.json')
        if jsonfile:
            polling_data = parse_cec_mayor(jsonfile["TC"])
            gen_mayor(polling_data)
            # return
        else:
            sht_data, source = parse_tv_sht()
            if 'cec' not in source.values():
                gen_tv_mayor(source, sht_data)
    else:
        gen_mayor()# default
        gen_tv_mayor()
