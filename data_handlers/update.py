'''
    Update the election result into WHORU GQL Server
'''
import os
import data_handlers.gql.variable as variable
import data_handlers.gql.query as query
from data_handlers.gql.tool import gql_fetch, gql_update 
from tools.cec_data import request_url

gql_endpoint = os.environ['GQL_URL']
BUCKET = os.environ['BUCKET']          ### expected: whoareyou-gcs.readr.tw
ENV_FOLDER = os.environ['ENV_FOLDER']  ### expected: elections[-dev]

def show_update_person(result, id):
    if result:
        result  = result['item']
        tks     = result['votes_obtained_number']
        tksRate = result['votes_obtained_percentage']
        elected = result['elected']
        print(f'Update election person id={id} to tks={tks}, tksRate={tksRate}, and elected={elected}')

def show_update_party(result, id):
    if result:
        result  = result['item']
        tks      = result['votes_obtained_number']
        tksRate1 = result['first_obtained_number']
        tksRate2 = result['second_obtained_number']
        seats = result['seats']
        print(f'Update election person id={id} to tks={tks}, tksRate1={tksRate1}, tksRate2={tksRate2}, and seats={seats}')


def update_person_election(year: str, election_type:str):
    '''
        Give the year of election, and update the person election result into WHORU database
    '''
    allowed_election_type = ['president', 'mountainIndigenous', 'plainIndigenous']
    if election_type not in allowed_election_type:
        print(f'election_type: {election_type} is not allowed')
        return False
    url_mapping = {
        'president': f'https://{BUCKET}/{ENV_FOLDER}/v2/{year}/president/all.json',
        'mountainIndigenous': f'https://{BUCKET}/{ENV_FOLDER}/v2/{year}/legislator/mountainIndigenous/all.json',
        'plainIndigenous': f'https://{BUCKET}/{ENV_FOLDER}/v2/{year}/legislator/plainIndigenous/all.json'
    }
    query_mapping = {
        'president': query.get_president_string(year),
        'mountainIndigenous': query.get_mountain_indigeous_string(year),
        'plainIndigenous': query.get_plain_indigeous_string(year)
    }

    ### Catch the v2 json, which records all the election result
    v2_url = url_mapping[election_type]
    raw_data = request_url(v2_url)
    if raw_data==None:
        print("Can't get v2 president json")
        return False
    v2_data = raw_data['candidates']

    ### Create the mapping table for id and candNo
    gql_presidents = gql_fetch(gql_endpoint, query_mapping[election_type])
    mapping = {} # {candNo: [id]}
    for data in gql_presidents['personElections']:
        id     = str(data['id'])
        candNo = str(data['number'])
        subId_list = mapping.setdefault(candNo, [])
        subId_list.append(id)
    
    ### Parse the data in v2
    for data in v2_data:
        candNo      = data['candNo']
        tks         = data['tks']
        tksRate     = data['tksRate']
        candVictor  = (data['candVictor']==True)
        ids = mapping.get(str(candNo), [])
        for id in ids:
            gql_variable = variable.PersonVariable(
                votes_obtained_number     = f'{tks}',
                votes_obtained_percentage = f'{tksRate}%',
                elected                   = candVictor,
                id                        = id
            ).to_json()
            result = gql_update(gql_endpoint, query.gql_update_person, gql_variable)
            show_update_person(result, id)
    return True

def update_party_election(year: str):
    '''
        Give the year of election, and update the party election result into WHORU database
    '''
    v2_url = f'https://{BUCKET}/{ENV_FOLDER}/v2/{year}/legislator/party/all.json'
    query_string = query.get_party_string(year)

    ### Catch the v2 json, which records all the election result
    raw_data = request_url(v2_url)
    if raw_data==None:
        print("Can't get v2 president json")
        return False
    v2_data = raw_data['parties']

    ### Create the mapping table for id and candNo
    gql_presidents = gql_fetch(gql_endpoint, query_string)
    mapping = {} # {candNo: [id]}
    for data in gql_presidents['organizationsElections']:
        id     = str(data['id'])
        candNo = str(data['number'])
        mapping[candNo] = id
    
    ### Parse the data in v2
    for data in v2_data:
        candNo       = data['candNo']
        tks          = data['tks']
        tksRate1     = data['tksRate1']
        tksRate2     = data['tksRate2']
        seats        = data['seats']
        id           = mapping.get(str(candNo), None)
        if id!=None:
            gql_variable = variable.PartyVariable(
                votes_obtained_number     = f'{tks}',
                first_obtained_number     = f'{tksRate1}%',
                second_obtained_number    = f'{tksRate2}%',
                seats                     = f'{seats}',
                id                        = id
            ).to_json()
            result = gql_update(gql_endpoint, query.gql_update_party, gql_variable)
            show_update_party(result, id)
    return True


