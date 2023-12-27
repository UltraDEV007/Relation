import data_handlers.queries as query
import asyncio
import os

gql_endpoint = os.environ['WHORU_GQL_PROD']

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