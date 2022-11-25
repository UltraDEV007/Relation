from datetime import datetime, timedelta
import json
import os
from tools.uploadGCS import save_file, upload_multiple_folders
from tools.cec_data import request_cec_by_type
from configs import districts_mapping, default_seat, default_seat_name

with open('mapping/mapping_county_town.json', encoding='utf-8') as f:
    mapping_county_town = json.loads(f.read())
with open('mapping/mapping_county_area_town_vill.json', encoding='utf-8') as f:
    mapping_county_area_town_vill = json.loads(f.read())
with open('mapping/mapping_county_town_vill.json', encoding='utf-8') as f:
    mapping_county_town_vill = json.loads(f.read())
with open('mapping/councilMember_candidate_2022.json', encoding='utf-8') as f:
    candidate_info = json.loads(f.read())


VOTES = 'prof3'
ELEGIBLE_VOTERS = 'prof7'
ENV_FOLDER = os.environ['ENV_FOLDER']
IS_TV = os.environ['PROJECT'] == 'tv'
IS_STARTED = os.environ['IS_STARTED'] == 'true'
POLITICS_URL = os.environ['POLITICS_URL']


def parse_cec_council(raw_data):
    organized_data = {}
    for district in raw_data:
        county_code = f"{district['prvCode']}_{district['cityCode']}_000"
        county = organized_data.setdefault(county_code, {"area": {}, "town": {}})
        if district['deptCode'] is None or district['deptCode'] == '000':
            region_code = district['areaCode']
            region = county["area"].setdefault(region_code, {'detailed': {
                VOTES: district[VOTES],
                ELEGIBLE_VOTERS: district[ELEGIBLE_VOTERS],
                'profRate': district['profRate'],
            }})
        elif district['liCode'] is None or district['liCode'] == '000':
            # region_code = f"{district['prvCode']}_{district['cityCode']}_{district['deptCode']}"
            region_code = f"{district['areaCode']}{district['deptCode']}"
            region = county["town"].setdefault(region_code, {'detailed': {
                VOTES: district[VOTES],
                ELEGIBLE_VOTERS: district[ELEGIBLE_VOTERS],
                'profRate': district['profRate'],
            }})
        for c in district['candTksInfo']:
            candNo = region.setdefault(c['candNo'], c)
            candNo = c
    return organized_data


def gen_seat(updatedAt, county_code, polling_data):
    result = []
    parties = {default_seat_name: default_seat[county_code]}
    if polling_data:
        for area_code, area in polling_data[county_code]["area"].items():
            for canNo, candidate in area.items():
                if canNo == 'detailed':
                    continue
                if candidate['candVictor'] == '*' or candidate['candVictor'] == '!':
                    try:
                        party = candidate_info[county_code][area_code][str(
                            canNo).zfill(2)]['party']
                    except KeyError:
                        continue
                    party = party if party != '無' else '無黨籍及未經政黨推薦'
                    parties[default_seat_name] -= 1
                    if party in parties:
                        parties[party] += 1
                    else:
                        parties[party] = 1
    for party, count in parties.items():
        if count:
            result.append({
                "label": party,
                "seats": count,
            })
        result = sorted(result, key=lambda x: x['seats'], reverse=True)
    year = datetime.now().year
    destination_file = f'{ENV_FOLDER}/{year}/councilMember/seat/county/{county_code[:-4].replace("_", "")}.json'
    data = {"updatedAt": updatedAt,
            "parties": result}
    save_file(destination_file, data, year)
    return


def gen_vote(updatedAt, county_code, polling_data, year, candidate_info=candidate_info):
    result = []
    if polling_data:
        polling_data = polling_data[county_code]["area"]
    for region_code, region_candidates in candidate_info[county_code].items():
        candidates = []
        for candNo, c_info in region_candidates.items():
            if candNo == 'type':
                continue
            candTks = {
                'candNo': candNo.lstrip('0'),
                'name': {
                    'label': c_info['name'],
                    'href': f"{POLITICS_URL}/person/{c_info['name_id']}",
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
                    cand_polling_data = polling_data[region_code][int(candNo)]
                except KeyError:
                    try:
                        cand_polling_data = polling_data[region_code][candNo]
                    except KeyError:
                        continue
                candTks['tks'] = cand_polling_data['tks'] if cand_polling_data['tks'] else 0
                candTks['tksRate'] = cand_polling_data['tksRate'] if cand_polling_data['tksRate'] else 0
                candTks['candVictor'] = True if cand_polling_data['candVictor'] == '*' or cand_polling_data['candVictor'] == True else False
            candidates.append(candTks)
        result.append(
            {"districtName": region_code,
             "type": region_candidates['type'],
             "candidates": candidates})

    VERSION = os.environ['VERSION']
    try:
        english_districts_name = districts_mapping[mapping_county_town[county_code]]
    except KeyError:
        english_districts_name = districts_mapping[county_code]
    try:
        chinese_districts_name = mapping_county_town[county_code]
    except KeyError:
        chinese_districts_name = county_code
    data = {"updatedAt": updatedAt,
            "year": str(year),
            "type": 'councilMember',
            "title": f"縣市議員選舉({chinese_districts_name})",
            "version": VERSION,
            "districts": result}
    destination_file = f'{ENV_FOLDER}/{VERSION}/{year}/councilMember/{english_districts_name}.json'

    save_file(destination_file, data, year)
    return


def map_candidate(region_candidates, polling_data):
    candidates = []
    for candNo, c_info in region_candidates.items():
        if candNo == 'type':
            continue
        candTks = {
            "candNo": int(candNo),
            "name": c_info['name'],
            "party": c_info['party'] if c_info['party'] != '無' else '無黨籍',
            "tksRate": 0,
            "candVictor": " "
        }
        if polling_data:
            try:
                can_polling_data = polling_data[int(candNo)]
                candTks['tks'] = can_polling_data['tks'] if can_polling_data['tks'] else 0
                candTks['tksRate'] = can_polling_data['tksRate'] if can_polling_data['tksRate'] else 0
                candTks['candVictor'] = can_polling_data['candVictor'] if can_polling_data['candVictor']else ' '
            except KeyError:
                continue
        candidates.append(candTks)

    return candidates


def gen_map(updatedAt, county_code, polling_data, scope='', scope_code='', sub_region='', area_code='', year = datetime.now().year, is_running = False):
    result = {'normal': [], 'indigenous': []}
    county_votes = 0
    county_eligible_voters = 0
    if scope == 'county':
        summary = {'normal': [], 'indigenous': []}
        for area_code, towns in sub_region.items():
            summary_range = f'{mapping_county_town[county_code]} 第{area_code}選區'
            candidate_info_scope = candidate_info[county_code][area_code]
            if polling_data:
                area_polling = polling_data[county_code]["area"][area_code]
                candidates = map_candidate(candidate_info_scope, area_polling)
                profRate = area_polling['detailed']['profRate'] if area_polling['detailed']['profRate'] else 0
                # county_votes += area_polling['detailed'][VOTES]
                # county_eligible_voters += area_polling['detailed'][ELEGIBLE_VOTERS]
            else:
                candidates = map_candidate(candidate_info_scope, '')
                profRate = 0
            summary_district = {
                "range": summary_range,
                "county": county_code[:-4].replace("_", ""),
                "area": None if area_code == '00' else area_code,
                "town": None,
                "vill": None,
                "type": candidate_info_scope['type'],
                "profRate": profRate,
                "candidates": candidates}
            if candidate_info_scope['type'] == 'normal':
                summary['normal'].append(summary_district)
            else:
                summary['indigenous'].append(summary_district)
            for region_code in towns:
                town_code = region_code
                vill_code = '000'
                range = f'{mapping_county_town[county_code]} {mapping_county_town[f"{county_code[:-3]}{town_code}"]}'
                candidate_info_scope = candidate_info[county_code][area_code]

                if polling_data:
                    town_polling = polling_data[county_code]["town"][f"{area_code}{town_code}"]
                    candidates = map_candidate(candidate_info_scope, town_polling)
                    profRate = town_polling['detailed']['profRate'] if town_polling['detailed']['profRate'] else 0
                    county_votes += town_polling['detailed'][VOTES]
                    county_eligible_voters += town_polling['detailed'][ELEGIBLE_VOTERS]
                else:
                    candidates = map_candidate(candidate_info_scope, '')
                    profRate = 0
                district = {
                    "range": range,
                    "county": county_code[:-4].replace("_", ""),
                    "area": None if area_code == '000' else area_code,
                    "town": None if town_code == '000' else town_code,
                    "vill": None if vill_code == '000' else vill_code,
                    "type": candidate_info_scope['type'],
                    "profRate": profRate,
                    "candidates": candidates}
                if candidate_info_scope['type'] == 'normal':
                    result['normal'].append(district)
                else:
                    result['indigenous'].append(district)

    else:
        for region_code in sub_region.keys():
            town_code = scope_code
            vill_code = region_code
            range = sub_region[region_code].replace("_", " ")
            candidate_info_scope = candidate_info[county_code][area_code]
            if polling_data:
                vill_polling = polling_data[county_code][area_code][town_code][vill_code]
                candidates = map_candidate(candidate_info_scope, vill_polling)
                profRate = vill_polling['detailed']['profRate'] if vill_polling['detailed']['profRate'] else 0
            else:
                candidates = None
                profRate = None
            district = {
                "range": range,
                "county": county_code[:-4].replace("_", ""),
                "area": None if area_code == '000' else area_code,
                "town": None if town_code == '000' else town_code,
                "vill": None if vill_code == '000' else vill_code,
                "type": candidate_info_scope['type'],
                "profRate": profRate,
                "candidates": candidates}
            if candidate_info_scope['type'] == 'normal':
                result['normal'].append(district)
            else:
                result['indigenous'].append(district)
    for type in result:
        if result[type]:
            if scope == 'county':
                data = {"updatedAt": updatedAt,
                        "is_running": is_running,
                        'summary': {
                            "range": mapping_county_town[county_code],
                            "county": county_code[:-4].replace('_', ''),
                            "town": None,
                            "vill": None,
                            "profRate": round(county_votes / county_eligible_voters * 100, 2) if county_eligible_voters else 0,
                            "districts": summary[type]
                        },
                        "districts": result[type]}
            else:
                data = {"updatedAt": updatedAt,
                        "is_running": is_running,
                        "districts": result[type]}
            dest_county = county_code[:-3].replace("_", "")
            if scope == 'county':
                destination_file = f'{ENV_FOLDER}/{year}/councilMember/map/{scope}/{type}/{dest_county}.json'
            else:
                destination_file = f'{ENV_FOLDER}/{year}/councilMember/map/{scope}/{type}/{dest_county}{town_code}.json'
            save_file(destination_file, data, year)
    return


def gen_councilMember(updatedAt = '', data = '', is_running = False):
    updatedAt = updatedAt if updatedAt else (datetime.utcnow() + timedelta(hours = 8)).strftime('%Y-%m-%d %H:%M:%S')
    year = datetime.now().year
    for county_code, areas in mapping_county_area_town_vill.items():
        county_code = county_code + '_000'
        gen_vote(updatedAt, county_code, data, year)
        if IS_TV:
            continue
        gen_seat(updatedAt, county_code, data)
        gen_map(updatedAt, county_code, data, 'county', county_code, areas, is_running)
        if IS_STARTED:
            continue
        for area_code, towns in areas.items():
            for town_code, vills in towns.items():
                updatedAt = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
                gen_map(updatedAt, county_code, data,
                        'town', town_code, vills, area_code)

    return


if __name__ == '__main__':
    if IS_STARTED:
        jsonfile, is_running = request_cec_by_type()
        if jsonfile:
            updatedAt = datetime.strptime(jsonfile["ST"], '%m%d%H%M%S')
            updatedAt = f"{datetime.now().year}-{datetime.strftime(updatedAt, '%m-%d %H:%M:%S')}"
            council_data = parse_cec_council(
                jsonfile["T1"] + jsonfile["T2"] + jsonfile["T3"])
            gen_councilMember(updatedAt, council_data, is_running)
            print("councilMember done")
        else:
            print('problem of cec data ')
    else:
        gen_councilMember()
        print("councilMember done")
    # upload_multiple_folders(datetime.now().year)