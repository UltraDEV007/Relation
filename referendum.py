import os
import json
from datetime import datetime, timedelta
from tools.cec_data import request_cec_by_type
from tools.uploadGCS import save_file
ENV_FOLDER = '/usr/src/app/gcs/' + os.environ['ENV_FOLDER']
IS_STARTED = os.environ['IS_STARTED'] == 'true'

with open('mapping/mapping_county_town.json', encoding='utf-8') as f:
    mapping_county_town = json.loads(f.read())
with open('mapping/mapping_county_town_vill.json', encoding='utf-8') as f:
    mapping_county_town_vill = json.loads(f.read())
with open('mapping/referendum_topic.json', encoding='utf-8') as f:
    referendum_topic = json.loads(f.read())


def parse_cec_referendum(raw_data):
    organized_data = {}
    for case_id, data in raw_data.items():
        if case_id == 'ST':
            continue
        for district in data:
            prvCode = district['prvCode'] if district['prvCode'] else '000'
            cityCode = district['cityCode'] if district['cityCode'] else '000'
            deptCode = district['deptCode'] if district['deptCode'] else '000'
            region_code = f"{prvCode}_{cityCode}_{deptCode}"
            case = organized_data.setdefault(case_id, {})
            case.setdefault(region_code, district)
            case[region_code] = district
    return organized_data


def gen_vote(updatedAt, polling_data='', year=datetime.now().year):
    result = []
    if polling_data:
        for case_name, all_data in polling_data.items():
            case = referendum_topic[case_name]
            county_data = all_data["00_000_000"]
            proposition = {
                "no": case["no"],
                "content": case["content"],
                "planner": case["planner"],
                "agreeTks": county_data["agreeTks"] if county_data["agreeTks"] else 0,
                "agreeRate": county_data["agreeRate"] if county_data["agreeRate"] else 0,
                "disagreeTks": county_data["disagreeTks"] if county_data["disagreeTks"] else 0,
                "disagreeRate": county_data["disagreeRate"] if county_data["disagreeRate"] else 0,
                "pass": True if county_data["adptVictor"] == "Y" else False
            }
            result.append(proposition)
    else:
        case = referendum_topic["F1"]
        result.append(
            {"no": case["no"],
                "content": case["content"],
                "planner": case["planner"],
                "agreeTks": 0,
                "agreeRate": 0,
                "disagreeTks": 0,
                "disagreeRate": 0,
                "pass": True}
        )
    VERSION = os.environ['VERSION']
    data = {
        "updatedAt": updatedAt,
        "year": year,
        "type": "referendum",
        "version": VERSION,
        "title": "公投選舉",
        "propositions": result
    }
    destination_file = f'{ENV_FOLDER}/{VERSION}/{year}/referendum/all.json'

    save_file(destination_file, data, year)
    return


def gen_map(updatedAt, case_id, scope, polling_data,  scope_code, sub_region, county='', year=datetime.now().year, is_running=False):
    result = []
    for region_code in sub_region:
        town_code = None
        vill_code = None
        if scope == 'country':
            region_code = f"{region_code}_000"
            range = mapping_county_town[region_code]
            county_code = region_code.replace('_', '')[:-3]
        elif scope == 'county':
            town_code = region_code
            region_code = f"{scope_code}_{region_code}"
            range = f'{mapping_county_town[f"{scope_code}_000"] } {mapping_county_town[region_code]}'
            county_code = scope_code.replace('_', '')
        else:
            range = sub_region[region_code].replace('_', ' ')
            county_code = county.replace('_', '')
            town_code = scope_code
            vill_code = region_code
            region_code = f"{county}_{town_code}_{vill_code}"

        tks_info = {
            "range": range,
            "county": county_code,
            "town": town_code,
            "vill": vill_code,
            "profRate": 0,
            "agreeRate": 0,
            "disagreeRate": 0,
            "adptVictor": 'Y',
        }
        if scope == 'town':
            tks_info['profRate'] = None
        if polling_data:
            case_polling = polling_data[case_id]
            region_polling = case_polling[region_code]
            tks_info['profRate'] = region_polling['profRate']
            tks_info['agreeRate'] = region_polling['agreeRate']
            tks_info['disagreeRate'] = region_polling['disagreeRate']
            tks_info['adptVictor'] = region_polling['adptVictor']

        result.append(tks_info)
    data = {"updatedAt": updatedAt,
            "is_running": is_running,
            "is_started": IS_STARTED,
            "districts": result}

    if scope == 'country':
        data['summary'] = {
            "range": '全國',
            "county": None,
            "town": None,
            "vill": None,
            "profRate": 0,
            "agreeRate": 0,
            "disagreeRate": 0,
            "adptVictor": 'Y',
        }
        if polling_data:
            country_polling = polling_data[case_id]['00_000_000']
            data['summary']['profRate'] = country_polling['profRate']
            data['summary']['agreeRate'] = country_polling['agreeRate']
            data['summary']['disagreeRate'] = country_polling['disagreeRate']
            data['summary']['adptVictor'] = country_polling['adptVictor']
        destination_file = f'{ENV_FOLDER}/{year}/referendum/map/{case_id}/{scope}.json'
    elif scope == 'county':
        destination_file = f'{ENV_FOLDER}/{year}/referendum/map/{case_id}/{scope}/{county_code}.json'
    else:
        destination_file = f'{ENV_FOLDER}/{year}/referendum/map/{case_id}/{scope}/{county_code}{town_code}.json'

    save_file(destination_file, dict(sorted(data.items(), reverse=True)), year)
    return


def gen_referendum(updatedAt=(datetime.utcnow()+timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S'), data='', year=datetime.now().year, is_running=False):
    gen_vote(updatedAt, data, year)
    if IS_STARTED:
        cases = [case_id for case_id in data.keys()]
    else:
        cases = ["F1"]
    for case_id in cases:
        gen_map(updatedAt, case_id, 'country', data, '00_000_000', sub_region=[
                k for k in mapping_county_town_vill.keys()], year=year, is_running=is_running)
        for county_code, towns in mapping_county_town_vill.items():
            gen_map(updatedAt, case_id, 'county', data, county_code,
                    towns, year=year, is_running=is_running)
            if not IS_STARTED:
                for town_code, vills in towns.items():
                    gen_map(updatedAt, case_id, 'town', data, town_code,
                            vills, county_code, year=year, is_running=is_running)

    return


if __name__ == "__main__":
    if IS_STARTED:
        referendumfile, is_running = request_cec_by_type('rf')
        if referendumfile:
            polling_data = parse_cec_referendum(referendumfile)
            updatedAt = datetime.strptime(referendumfile["ST"], '%m%d%H%M%S')
            updatedAt = f"{datetime.now().year}-{datetime.strftime(updatedAt, '%m-%d %H:%M:%S')}"
            gen_referendum(updatedAt, polling_data, is_running=is_running)
            print("referendum done")
        else:
            print('problem of cec referendum data ')
    else:
        gen_referendum()
        print("referendum done")
    # upload_multiple_folders()
