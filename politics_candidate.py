import json
import os
from configs import districts_mapping, election_types, upload_configs
from tools.query import query_elections, query_personElections
from tools.uploadGCS import upload_blob


def rm_redundant_districtName(name, district):
    name = name.split('第')
    elec_dist_num_str = name[1].replace("選區", "")
    elec_dist_num_str = elec_dist_num_str.replace("選舉區", "")
    return elec_dist_num_str


def candidate_process(data, person_number_sort, districts, district):
    candidate = {
        "number": None,
        "name": {
            "label": "",
            "href": "",
            "imgSrc": ""
        },
        "party": {
            "label": "",
            "href": "",
            "imgSrc": ""
        },
        "votes": None,
        "voteRate": None,
        "elected": None

    }
    if data['electoral_district']:
        type = data['electoral_district']['indigenous']
        if type is None:
            type = 'normal'

        districtName = data['electoral_district']['name']
        if '第' in districtName:
            districtName = rm_redundant_districtName(districtName, district)
        # elec_dist_num = elec_dist_num_process(
        #     data['electoral_district']['name'], district)
    if data['number']:
        candidate['number'] = int(data['number'])
    else:
        person_number_sort = False
    if data['person_id']:
        candidate['name']['label'] = data['person_id']['name']
        candidate['name']['href'] = f"./person/{data['person_id']['id']}"
        candidate['name']['imgSrc'] = data['person_id']['image'] if data['person_id']['image'] else ""
    if data['party']:
        # candidate['party']['href'] = f"./organizations/{data['party']['id']}" #open while organization page existed
        candidate['party']['label'] = data['party']['name']
        candidate['party']['imgSrc'] = data['party']['image'] if data['party']['image'] else ""
    if data['votes_obtained_number']:
        candidate['votes'] = int(data['votes_obtained_number'])
    if data['votes_obtained_percentage']:
        voteRate = data['votes_obtained_percentage'].replace('%', '')
        candidate['voteRate'] = float(voteRate)
    if data['elected']:
        candidate['elected'] = data['elected']

    if districtName in districts:
        districts[districtName]["candidates"].append(candidate)
    else:
        districts[districtName] = {
            "type": type, "districtName": districtName, "candidates": [candidate]}
    return person_number_sort


def generate_politic_candidate():
    for election_type in election_types:
        if election_type != '縣市議員':
            continue
        all_elections = query_elections(election_type)
        election_type = election_types.get(election_type)
        print(all_elections)
        for year in all_elections:
            # if year != 2018:
            #     continue
            election = all_elections[year]
            election_query_script = ','.join(
                ['{id:{equals:%s}}' % electionId for electionId in election])
            for district in districts_mapping.keys():
                districts = {}
                personElections_data = query_personElections(
                    district, election_query_script)
                person_number_sort = True
                if personElections_data:
                    for personElection_data in personElections_data:
                        if not candidate_process(personElection_data, person_number_sort, districts, district):
                            person_number_sort = False
                    districts_election = {"districts": []}

                    for v in districts.values():
                        if person_number_sort:
                            v["candidates"].sort(key=lambda x: x["number"])
                        districts_election["districts"].append(v)
                    districts_election["districts"].sort(
                        key=lambda x: x["districtName"])
                    destination_file = f'elections/{year}/{election_type}/{districts_mapping[district]}.json'
                    if not os.path.exists(os.path.dirname(destination_file)):
                        os.makedirs(os.path.dirname(destination_file))
                    with open(destination_file, 'w') as f:
                        f.write(json.dumps( districts_election, ensure_ascii=False))
                    upload_blob(destination_file, year)
if __name__ == '__main__':
    generate_politic_candidate()