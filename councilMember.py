from datetime import datetime
import json
import os
from tools.uploadGCS import save_file
from tools.cec_data import request_cec
from configs import districts_mapping

with open('mapping/mapping_county_town.json') as f:
    mapping_county_town = json.loads(f.read())
with open('mapping/mapping_county_area_town_vill.json') as f:
    mapping_county_area_town_vill = json.loads(f.read())
with open('mapping/councilMember_candidate_2022.json') as f:
    candidate_info = json.loads(f.read())
VOTES = 'prof3'
ELEGIBLE_VOTERS = 'prof7'
ENV_FOLDER = os.environ['ENV_FOLDER']


def parse_cec_council(raw_data):
    organized_data = {}
    for district in raw_data:
        if district['deptCode'] is None or district['deptCode'] == '000':
            county_code = f"{district['prvCode']}_{district['cityCode']}_000"
            region_code = district['areaCode']
            county = organized_data.setdefault(county_code, {})
            region = county.setdefault(region_code, {'detailed': {
                VOTES: district[VOTES],
                ELEGIBLE_VOTERS: district[ELEGIBLE_VOTERS],
                'profRate': district['profRate'],
            }})
            for c in district['candTksInfo']:
                candNo = region.setdefault(c['candNo'], c)
                candNo = c
    return organized_data


def gen_seat(county_code, polling_data):
    result = []
    parties = {}
    if polling_data:
        for area_code, area in polling_data[county_code].items():
            for canNo, candidate in area.items():
                if canNo == 'detailed':
                    continue
                if candidate['candVictor'] == '*':
                    party = candidate_info[county_code][area_code][str(
                        canNo).zfill(2)]['party']
                    party = party if party != '無' else '無黨籍及未經政黨推薦'
                    if party in parties:
                        parties[party] += 1
                    else:
                        parties[party] = 1
        for party, count in parties.items():
            result.append({
                "label": party,
                "seats": count,
            })
    year = datetime.now().year
    destination_file = f'{ENV_FOLDER}/{year}/councilMember/seat/county/{county_code[:-4].replace("_", "")}.json'
    data = {"updatedAt": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "parties": result}
    save_file(destination_file, data, year)
    return


def gen_vote(county_code, polling_data, year, candidate_info = candidate_info):
    result = []
    if polling_data:
        polling_data = polling_data[county_code]
    for region_code, region_candidates in candidate_info[county_code].items():
        candidates = []
        for candNo, c_info in region_candidates.items():
            if candNo == 'type':
                continue
            candTks = {
                'candNo': candNo.lstrip('0'),
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
                try:
                    cand_polling_data = polling_data[region_code][int(candNo)]
                except KeyError:
                    try:
                        cand_polling_data = polling_data[region_code][candNo]
                    except KeyError:
                        continue
                candTks['tks'] = cand_polling_data['tks'] if cand_polling_data['tks'] else 0
                candTks['tksRate'] = cand_polling_data['tksRate'] if cand_polling_data['tksRate'] else 0
                candTks['candVictor'] = True if cand_polling_data['candVictor'] == '*' or  cand_polling_data['candVictor'] == True else False
            candidates.append(candTks)
        result.append(
            {"districtName": region_code,
             "type": region_candidates['type'],
             "candidates": candidates})

    # year = datetime.now().year
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    VERSION = os.environ['VERSION']
    try:
        english_districts_name = districts_mapping[mapping_county_town[county_code]]
    except KeyError:
        english_districts_name = districts_mapping[county_code]
    try:
        chinese_districts_name = mapping_county_town[county_code]
    except KeyError:
        chinese_districts_name = county_code
    data = {"updatedAt": now,
            "year": str(year),
            "type": 'mayor',
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

def gen_map(county_code, polling_data, scope='', scope_code='', sub_region=''):
    result = []
    county_votes = 0
    county_eligible_voters = 0
    for region_code in sub_region.keys():
        if scope == 'county':

            vill_code = '000'
            area_code = region_code
            range = f'{mapping_county_town[scope_code]} 第{region_code}選區'
            candidate_info_scope = candidate_info[county_code][region_code]

            if polling_data:
                area_polling = polling_data[county_code][area_code]
                candidates = map_candidate(
                    candidate_info_scope, area_polling)
                profRate = area_polling['detailed']['profRate'] if area_polling['detailed']['profRate'] else 0
                county_votes += area_polling['detailed'][VOTES]
                county_eligible_voters += area_polling['detailed'][ELEGIBLE_VOTERS]
            else:
                candidates = map_candidate(candidate_info_scope, '')
                profRate = 0
            result.append({
                "range": range,
                "county": county_code[:-4].replace("_", ""),
                "area": None if area_code == '000' else area_code,
                "vill": None if vill_code == '000' else vill_code,
                "type": candidate_info_scope['type'],
                "profRate": profRate,
                "candidates": candidates})
        else:
            town_code = region_code
            for vill_code, vill in sub_region[region_code].items():
                area_code = scope_code
                vill_name = vill.split("_")[-1]
                range = f'{mapping_county_town[county_code]} 第{region_code}選區 {vill_name}'
                candidate_info_scope = candidate_info[county_code][area_code]

                if polling_data:
                    vill_polling = polling_data[county_code][area_code][town_code][vill_code]
                    candidates = map_candidate(
                        candidate_info_scope, vill_polling)
                    profRate = vill_polling['detailed']['profRate'] if vill_polling['detailed']['profRate'] else 0
                else:
                    candidates = None
                    profRate = None
                result.append({
                    "range": range,
                    "county": county_code[:-4].replace("_", ""),
                    "area": None if area_code == '000' else area_code,
                    "vill": None if vill_code == '000' else vill_code,
                    "type": candidate_info_scope['type'],
                    "profRate": profRate,
                    "candidates": candidates})
    year = datetime.now().year
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data = {"updatedAt": now,
            "districts": result}
    if scope == 'county':
        data['summary'] = {
            "range": mapping_county_town[county_code],
            "county": county_code[:-4].replace('_', ''),
            "town": None,
            "vill": None,
            "profRate": round(county_votes / county_eligible_voters * 100, 2) if polling_data else 0
        }
    dest_county = county_code[:-3].replace("_", "")
    if scope == 'county':
        destination_file = f'{ENV_FOLDER}/{year}/councilMember/map/{scope}/{dest_county}.json'
    else:
        destination_file = f'{ENV_FOLDER}/{year}/councilMember/map/{scope}/{dest_county}{scope_code}.json'

    save_file(destination_file, dict(sorted(data.items(), reverse=True)), year)
    return


def gen_councilMember(data=''):
    year = datetime.now().year
    for county_code, areas in mapping_county_area_town_vill.items():
        county_code = county_code + '_000'
        print(mapping_county_town[county_code])
        gen_seat(county_code, data)
        gen_vote(county_code, data, year)
        gen_map(county_code, data, 'county', county_code, areas)
        if os.environ['isSTARTED'] != 'true':
            for area_code, towns in areas.items():
                print(area_code)
                gen_map(county_code, data, 'area', area_code, towns)
    return


if __name__ == '__main__':
    if os.environ['isSTARTED'] == 'true':
        # jsonfile = request_cec()
        with open('running.json') as f:
            jsonfile = json.loads(f.read())
        if jsonfile:
            # polling_data = parse_cec_mayor(jsonfile["TC"])
            # gen_mayor(polling_data)
            # print("mayor done")
            council_data = parse_cec_council(
                jsonfile["T1"] + jsonfile["T2"] + jsonfile["T3"])
            gen_councilMember(council_data)
            print("councilMember done")

            # return 'done'
        # return 'problem of cec data '
    else:
        # gen_mayor()
        # print("mayor done")
        gen_councilMember()

        # return 'done'
