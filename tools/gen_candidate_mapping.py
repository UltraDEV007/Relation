from conn import gql_client
from gql import gql
import json 
with open('mapping/mapping_county_town_vill.json') as f:
    mapping_county_town_vill = json.loads(f.read())
with open('mapping/mapping_county_town.json') as f:
        mapping_county_town = json.loads(f.read())
sort_county = ["臺北市","新北市","桃園市","臺中市","臺南市","高雄市","基隆市","新竹縣","新竹市","苗栗縣","彰化縣","南投縣","雲林縣","嘉義縣","屏東縣","宜蘭縣","花蓮縣","臺東縣","澎湖縣","金門縣","連江縣",]
sort_county_code = ['63_000_000', '65_000_000', '68_000_000', '66_000_000', '67_000_000', '64_000_000', '10_017_000', '10_004_000', '10_018_000', '10_005_000', '10_007_000', '10_008_000', '10_009_000', '10_010_000', '10_013_000', '10_002_000', '10_015_000', '10_014_000', '10_016_000', '09_020_000', '09_007_000']
query = '''
     query{
    personElections(where:{
        election:{type:{in: "%s"}, election_year_year:{equals:%s}},
    }){
    number
    votes_obtained_number
    votes_obtained_percentage
    elected
    electoral_district{
        name
        city
        indigenous
    }
    party{
        id
        name
        image
    }
    person_id{
        id
        name
        image
        }
    }
    }'''
client = gql_client()

def get_mayor_candidate_from_cms(year): #electoral_district:{name:{contains:"%s"}},
    country = {i: {} for i in sort_county_code}
    global query
    query = query % ('縣市首長', year)
    print(query)
    r = client.execute(gql(query))

    if r['personElections']:
        for candidate in r['personElections']:
            city_name = candidate['electoral_district']['city']
            city_code = [k for k in mapping_county_town.keys()][[v for v in mapping_county_town.values()].index(city_name)]
            # city_code = candidate['electoral_district']['city']
            candNo = int(candidate['number'])
            candidate_info = {}

            candidate_info['name'] = candidate['person_id']['name']
            candidate_info['name_id'] = candidate['person_id']['id']
            candidate_info['name_img'] = candidate['person_id']['image'] if candidate['person_id']['image'] else ''
            candidate_info['party'] = candidate['party']['name'] if candidate['party'] else '無'
            candidate_info['party_id'] = candidate['party']['id'] if candidate['party'] else ''
            candidate_info['party_img'] = candidate['party']['image'] if candidate['party'] else ''
            candidate_info['tks'] = int(candidate['votes_obtained_number']) if candidate['votes_obtained_number'] else 0
            candidate_info['tksRate'] = float(candidate['votes_obtained_percentage'].replace('%', '')) if candidate['votes_obtained_percentage'] else 0
            candidate_info['candVictor'] = candidate['elected']        
            city = country.setdefault(city_code, {candNo: candidate_info})
            city[candNo] = candidate_info
    for city, candidates in country.items():
        country[city] = dict(sorted(candidates.items()))
        

    with open('mapping/mayor_candidate_2022.json', 'w') as f:
        f.write(json.dumps(country, ensure_ascii=False))
        # f.write(json.dumps(dict(sorted(country.items())), ensure_ascii=False))
    return 


def get_councilMember_from_cms(year):
    country = {i: {} for i in sort_county_code}
    global query
    query = query % ('縣市議員', year)
    # print(query)
    r = client.execute(gql(query))

    if r['personElections']:
        for candidate in r['personElections']:
            city_name = candidate['electoral_district']['city']
            area_name = candidate['electoral_district']['name'].replace('選舉區', '')
            area_name = area_name.replace('選區', '')
            area_code = area_name.replace(f'{city_name}第', '').zfill(2)
            city_code = [k for k in mapping_county_town.keys()][[v for v in mapping_county_town.values()].index(city_name)]
            indigenous = candidate['electoral_district']['indigenous']
            
            candNo = str(candidate['number']).zfill(2)
            candidate_info = {}
            candidate_info['name'] = candidate['person_id']['name']
            candidate_info['name_id'] = candidate['person_id']['id']
            candidate_info['name_img'] = candidate['person_id']['image'] if candidate['person_id']['image'] else ''
            candidate_info['party'] = candidate['party']['name'] if candidate['party'] else '無'
            candidate_info['party_id'] = candidate['party']['id'] if candidate['party'] else ''
            candidate_info['party_img'] = candidate['party']['image'] if candidate['party'] else ''
            candidate_info['tks'] = int(candidate['votes_obtained_number']) if candidate['votes_obtained_number'] else 0
            candidate_info['tksRate'] = float(candidate['votes_obtained_percentage'].replace('%', '')) if candidate['votes_obtained_percentage'] else 0
            candidate_info['candVictor'] = candidate['elected']        
            city = country.setdefault(city_code, {})
            area = city.setdefault(area_code, {'type':indigenous})
            area[candNo] = candidate_info
    for city, areas in country.items():
        for area, candidates in areas.items():
            country[city][area] = dict(sorted(candidates.items()))
        country[city] = dict(sorted(areas.items()))
        
        

    with open('mapping/councilMember_candidate_2022.json', 'w') as f:
        f.write(json.dumps(country, ensure_ascii=False))
    return 
def gen_councilMember_county_area_vill_mapping():
    country = {}
    with open('running.json') as f:
        running = json.loads(f.read())
    data = running['T1'] + running['T2'] + running['T3']
    for dist in data:
        if dist['deptCode']:
            county_code = dist['prvCode'] + '_' + dist['cityCode']
            area_code = dist['areaCode']
            town_code = dist['deptCode']
            county = country.setdefault(county_code, {})
            area = county.setdefault(area_code,{})
            area[town_code] = mapping_county_town_vill[county_code][town_code]

    with open('mapping/mapping_county_area_town_vill.json', 'w') as f:
        # f.write(json.dumps(dict(sorted(country.items())), ensure_ascii=False))
        f.write(json.dumps(country, ensure_ascii=False))
    return 
            

if __name__ == '__main__':

    year = '2022'
    # gen_councilMember_county_area_vill_mapping()
    # get_mayor_candidate_from_cms(year)
    # get_councilMember_from_cms(year)

