import data_handlers.queries as query
import asyncio
import os
import data_handlers.helpers as hp
import re

gql_endpoint = os.environ['GQL_URL']

def adapter_president_v2():
    '''
    Description:
        Fetch the presidents data in the GQL database and organize them into the
        structure we desire. If the candNo doesn't exist in the data resource, we'll
        automatically create a mock one.
    Output:
        {
            "candNo": {
                "first": 正總統資料(包含名稱與政黨),
                "second": 副總統資料(包含名稱與政黨),
            }
        }
    '''
    mapping_president    = {}
    gql_presidents = query.gql2json(gql_endpoint, query.gql_president_2024)
    
    gql_data = gql_presidents['personElections']
    for idx, data in enumerate(gql_data):
        candNo      = data.get('number', str(idx+1))  ###如果實際candNo尚不存在，使用idx作為假資料
        person_info = data.get('person_id', None)
        party_info  = data.get('party', None)
        if person_info == None:
            continue
        ### vice president
        if data.get('mainCandidate'):
            sub = mapping_president.setdefault(candNo, {})
            sub['second'] = {
                'person': person_info,
                'party': party_info
            }
        else:
            sub = mapping_president.setdefault(candNo, {})
            sub['first'] = {
                'person': person_info,
                'party': party_info
            }
    return mapping_president

def adapter_indigeous_v2(gql_president):
    mapping_indigeous    = {}
    gql_data = gql_president['personElections']
    for idx, data in enumerate(gql_data):
        candNo      = data.get('number', str(idx+1))  ###如果實際candNo尚不存在，使用idx作為假資料
        person_info = data.get('person_id', None)
        party_info  = data.get('party', None)
        if person_info == None:
            continue
        if candNo == '':
            candNo = str(idx)
        mapping_indigeous[candNo] = {
            'person': person_info,
            'party': party_info,
        }
    return mapping_indigeous

def adapter_party_v2(gql_party):
    mapping_party    = {}
    gql_data = gql_party['organizationsElections']
    for idx, data in enumerate(gql_data):
        candNo      = data.get('number', str(idx+1))  ###如果實際candNo尚不存在，使用idx作為假資料
        party_info  = data.get('organization_id', None)
        if party_info == None:
            continue
        if candNo == '':
            candNo = str(idx)
        new_party_info = {}
        new_party_info['party'] = {
            "label": party_info.get('name', None),
            "href": None,
            "imgSrc": None,
        }
        mapping_party[candNo] = new_party_info
    return mapping_party

def adapter_constituency(gql_constituency):
    '''
        Create mapping_constituency_cand.json, which shows the hierarchy from city_code to candidates.
        <Example>
            mapping_constituency_cand = {
                '68000': {        => First level: cityCode(countyCode) [string]
                    '01': {       => Second level: areaCode [string]
                        1: DATA   => Third level: candNo [Int]
                    }
                    ...
                }
                ...
            }
    '''
    mapping_constituency_cand = {}
    person_data = gql_constituency['personElections']
    reverse_city_mapping = { value: key for key, value in hp.mapping_city.items() }
    pattern = r'\d+'  ###用來找選區編號
    for data in person_data:
        candNo = data['number']
        party_info  = data.get('party')
        party = party_info.get('name', None) if party_info else None
        person = data['person_id']
        city_code   = reverse_city_mapping[data['electoral_district']['city']]
        area_code   = re.findall(pattern, data['electoral_district']['name'])[0]

        subCity = mapping_constituency_cand.setdefault(city_code, {})
        subArea = subCity.setdefault(area_code, {})
        if candNo=='' or candNo==None:
            candNo = len(subCity[area_code])+1
        subCand = subArea.setdefault(candNo, {})
        subCand['party'] = party
        subCand['person'] = person
    return mapping_constituency_cand
