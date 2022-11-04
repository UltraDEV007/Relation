from datetime import datetime
import json
import os
from tools.uploadGCS import save_file
from tools.cec_data import request_cec
from configs import default_special_municipality

with open('mapping/mapping_county_town.json') as f:
    mapping_county_town = json.loads(f.read())
with open('mapping/mapping_county_town_vill.json') as f:
    mapping_county_town_vill = json.loads(f.read())
with open('mapping/mayor_candidate_2022.json') as f:
    candidate_info = json.loads(f.read())
VOTES = 'prof3'
ELEGIBLE_VOTERS = 'prof7'


def parse_cec_mayor(data):
    organized_data = {}
    for district in data:
        deptCode = district['deptCode'] if district['deptCode'] else '000'
        region_code = f"{district['prvCode']}_{district['cityCode']}_{deptCode}"
        region = organized_data.setdefault(region_code, {'detailed': {
            VOTES: district[VOTES],
            ELEGIBLE_VOTERS: district[ELEGIBLE_VOTERS],
            'profRate': district['profRate'],
        }})
        for c in district['candTksInfo']:
            candNo = region.setdefault(c['candNo'], c)
            candNo = c
    return organized_data


def gen_special_municipality(polling_data):
    result = []
    for county_code, default_candidates in default_special_municipality.items():
        candidates = []
        if polling_data:
            for candNo, c_info in candidate_info[county_code].items():
                tksRate = polling_data[county_code][int(
                    candNo)]['tksRate'] if polling_data[county_code][int(candNo)]['tksRate'] else 0
                tks = polling_data[county_code][int(
                    candNo)]['tks'] if polling_data[county_code][int(candNo)]['tks'] else 0
                candTks = {
                    "candNo": candNo.zfill(2),
                    "name": c_info['name'],
                    "party": c_info['party'],
                    "tks": tks,
                    "tksRate": tksRate,
                    "candVictor":  True if polling_data[county_code][int(candNo)]['candVictor'] == '*' else False,
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
    destination_file = f'elections/{year}/mayor/special_municipality.json'
    data = {"updatedAt": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "polling": result}
    save_file(destination_file, data, year)
    return


def gen_vote(polling_data=''):
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
                    'label': c_info['party'] if c_info['party'] != '無' else '',
                    'href': '',
                    'imgSrc': c_info['party_img'] if c_info['party_img'] else ''
                },
                'tks': 0,
                'tksRate': 0,
                'candVictor': False
            }
            if polling_data:
                candTks['tks'] = polling_data[region_code][int(
                    candNo)]['tks'] if polling_data[region_code][int(candNo)]['tks'] else 0
                candTks['tksRate'] = polling_data[region_code][int(
                    candNo)]['tksRate'] if polling_data[region_code][int(candNo)]['tksRate'] else 0
                candTks['candVictor'] = True if polling_data[region_code][int(
                    candNo)]['candVictor'] == '*' else False
            candidates.append(candTks)
        result.append(
            {"districtName": mapping_county_town[region_code], "candidates": candidates})

    year = datetime.now().year
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    VERSION = os.environ['VERSION']
    data = {"updatedAt": now,
            "year": str(year),
            "type": 'mayor',
            "title": "縣市長選舉",
            "version": VERSION,
            "districts": result}
    destination_file = f'elections/{VERSION}/{year}/mayor/all.json'

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
            can_polling_data = polling_data[region_code][int(candNo)]
            candTks['tks'] = can_polling_data['tks'] if can_polling_data['tks'] else 0
            candTks['tksRate'] = can_polling_data['tksRate'] if can_polling_data['tksRate'] else 0
            candTks['candVictor'] = can_polling_data['candVictor'] if can_polling_data['candVictor']else ' '
        candidates.append(candTks)

    return candidates


def gen_map(scope, polling_data,  scope_code='', sub_region=''):
    result = []
    country_votes = 0
    country_eligible_voters = 0
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
            region_code = scope_code +'_' + region_code  # vill code '09_007_010_010'
            range = sub_region[vill_Code].replace("_", " ")

        region_code_split = region_code.split('_')
        county_code = region_code_split[0] + '_' + region_code_split[1]
        town_code = region_code_split[2]

        candidates = map_candidate(candidate_info[f"{county_code}_000"], polling_data, region_code)
        if polling_data:
            detailed_polling_data = polling_data[region_code]['detailed']
            profRate = detailed_polling_data['profRate'] if detailed_polling_data['profRate'] else 0
            if scope == 'country': 
                country_votes += detailed_polling_data[VOTES]
                country_eligible_voters += detailed_polling_data[ELEGIBLE_VOTERS]
        else:
            profRate = 0
        
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
        data['summary'] = {
            "range": "全國",
            "county": None,
            "town": None,
            "vill": None,
            "profRate": round(country_votes / country_eligible_voters * 100, 2) if polling_data else 0
        }
        destination_file = f'elections/{year}/mayor/map/{scope}.json'
    elif scope == 'county':
        destination_file = f'elections/{year}/mayor/map/{scope}/{scope_code[:-3].replace("_", "")}.json'
    else:
        destination_file = f'elections/{year}/mayor/map/{scope}/{scope_code.replace("_", "")}.json'

    save_file(destination_file, dict(sorted(data.items(), reverse=True)), year)
    return
    


def gen_mayor(data = ''):
    print("全國")
    gen_special_municipality(data)
    gen_vote(data)
    gen_map('country', data, '00_000_000', candidate_info)
    for county_code, towns in mapping_county_town_vill.items():
        county_code = county_code + '_000'
        print(mapping_county_town[county_code])
        gen_map('county', data, county_code, towns)
        if os.environ['isSTARTED'] != 'true':
            for town_code, vills in towns.items():
                    town_code = county_code[:-3] + town_code
                    print(mapping_county_town[town_code])
                    gen_map('town', polling_data='', scope_code = town_code, sub_region=vills )
    return


if __name__ == '__main__':
    if os.environ['isSTARTED'] == 'true':
        jsonfile = request_cec()
        if jsonfile:
            polling_data = parse_cec_mayor(jsonfile["TC"])
            gen_mayor(polling_data)
    else:
        gen_mayor()# default