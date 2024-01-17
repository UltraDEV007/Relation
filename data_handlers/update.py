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
        print(f'Update {id} for tks={tks}, tksRate={tksRate}, and elected={elected}')

def update_president(year: str):
    '''
        Give the year of election, and update the president result into WHORU database
    '''
    ### Catch the v2 json, which records all the election result
    v2_president_url = f'https://{BUCKET}/{ENV_FOLDER}/v2/{year}/president/all.json'
    raw_data = request_url(v2_president_url)
    if raw_data==None:
        print("Can't get v2 president json")
        return False
    v2_president = raw_data['candidates']

    ### Create the mapping table for id and candNo
    gql_presidents = gql_fetch(gql_endpoint, query.get_president_string(year))
    mapping = {} # {candNo: [id]}
    for data in gql_presidents['personElections']:
        id     = str(data['id'])
        candNo = str(data['number'])
        subId_list = mapping.setdefault(candNo, [])
        subId_list.append(id)
    
    ### Parse the data in v2
    for data in v2_president:
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
            result = gql_update(gql_endpoint, query.gql_update_president, gql_variable)
            show_update_person(result, id)
    return True
    


