'''
    Update the election result into WHORU GQL Server
'''
import os
import re
import data_handlers.gql.variable as variable
import data_handlers.gql.query as query
import data_handlers.helpers as hp
from data_handlers.gql.tool import gql_fetch, gql_update 
from tools.cec_data import request_url

gql_endpoint = os.environ['GQL_URL']
BUCKET = os.environ['BUCKET']  
ENV_FOLDER = os.environ['ENV_FOLDER']

def update_person_election(year: str, election_type:str, gen_term_office: bool=False):
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

    ### Get the organization informations
    gql_organizations = gql_fetch(gql_endpoint, query.gql_organizations_string)
    organizations_table = {data['name']: data['id'] for data in gql_organizations['organizations']}

    ### Catch the v2 json, which records all the election result
    v2_url = url_mapping[election_type]
    raw_data = request_url(v2_url)
    if raw_data==None:
        print(f"Can't get v2 {election_type} json")
        return False
    v2_data = raw_data['candidates']

    ### Create the mapping table for id and candNo
    gql_person = gql_fetch(gql_endpoint, query_mapping[election_type])
    mapping_candNo_eid = {} # {candNo: {election_id: data}}
    for data in gql_person['personElections']:
        election_id  = str(data['id'])
        person_id    = str(data['person_id']['id'])
        candNo       = str(data['number'])
        is_vice      = data.get('mainCandidate', None)!=None
        subId_list   = mapping_candNo_eid.setdefault(candNo, {})
        subId_list[election_id] = {
            'person_id': person_id,
            'is_vice': is_vice,
        }

    ### Parse the data in v2
    for data in v2_data:
        candNo      = data['candNo']
        tks         = data['tks']
        tksRate     = data['tksRate']
        candVictor  = (data['candVictor']==True)
        election_ids = mapping_candNo_eid.get(str(candNo), {})
        for election_id, info in election_ids.items():
            gql_variable = variable.UpdatePersonElectionVariable(
                votes_obtained_number     = f'{tks}',
                votes_obtained_percentage = f'{tksRate}%',
                elected                   = candVictor,
                id                        = election_id
            ).to_json()
            result = gql_update(gql_endpoint, query.gql_update_person, gql_variable)
            show_update_person(result, election_type)
            
            ### If the candVictor==True, we need to update Person Organization
            if candVictor==True and gen_term_office==True:
                role, organization, term_office = '', '', {}
                person_id = info['person_id']
                is_vice   = info['is_vice']
                if election_type=='president':
                    role = '副總統' if(is_vice==True) else '總統'
                    organization = '總統府'
                    term_office = variable.termOffice_president_2024
                else:
                    role = '立委'
                    organization = '立法院'
                    term_office = variable.termOffice_legislator_2024
                organization_id = organizations_table[organization]
                gql_varible = variable.CreatePersonOrganizationVariable(
                    person_id = person_id,
                    organization_id = organization_id,
                    election_id = election_id,
                    role = role,
                    source = '中選會',
                    term_office = term_office
                ).to_json()
                result = gql_update(gql_endpoint, query.gql_create_personOrganization, gql_varible)
                show_create_personOrganization(result)
    return True

def update_party_election(year: str, gen_term_office: bool=False):
    '''
        Give the year of election, and update the party election result into WHORU database
        You should parse final_A json to get the person candidate winner.
    '''
    v2_url = f'https://{BUCKET}/{ENV_FOLDER}/v2/{year}/legislator/party/all.json'
    final_A_url = f'https://{BUCKET}/{ENV_FOLDER}/cec-data/final_A.json'

    ### Request v2 json, which records all the election result for organization election
    raw_data = request_url(v2_url)
    if raw_data==None:
        print("Can't get v2 party json")
        return False
    v2_data = raw_data['parties']

    ### Request final_A json, and the winner of person elections are inside M4 patyInfo
    final_A = request_url(final_A_url)
    if final_A==None:
        print("Can't get final_A json")
        return False
    patyInfo = final_A['M4'].get('patyInfo', [])

    ### Create the mapping table for organization as party
    query_string = query.get_party_oe_string(year)
    gql_party_oe = gql_fetch(gql_endpoint, query_string)
    mapping_party_oeid = {}   # oeid = organization election id
    mapping_party_oid  = {}   # oid  = organization id
    for data in gql_party_oe['organizationsElections']:
        party_oeid = str(data['id'])
        party_oid  = str(data['organization_id']['id'])
        candNo     = str(data['number'])
        mapping_party_oeid[candNo] = party_oeid
        mapping_party_oid[candNo]  = party_oid

    ### Create the mapping table for person, mapping relationship: partyId->legislatorOrder->Info
    query_string = query.get_party_pe_string(year)
    gql_party_pe = gql_fetch(gql_endpoint, query_string)
    mapping_person = {}
    for data in gql_party_pe['personElections']:
        election_id   = str(data['id'])
        party_oid     = str(data['party']['id'])
        person_id     = str(data['person_id']['id'])
        legislatorOrder = data['legislatoratlarge_number']
        subOrganization = mapping_person.setdefault(party_oid, {})
        subOrganization[legislatorOrder] = {
            'election_id': election_id,
            'person_id': person_id
        }

    ### Get the organization informations
    gql_organizations = gql_fetch(gql_endpoint, query.gql_organizations_string)
    organizations_table = {data['name']: data['id'] for data in gql_organizations['organizations']}
    
    ### Parse the data in v2
    for data in v2_data:
        candNo       = data['candNo']
        tks          = data['tks']
        tksRate1     = data['tksRate1']
        tksRate2     = data['tksRate2']
        seats        = int(data['seats'])
        party_oeid = mapping_party_oeid.get(str(candNo), None)
        if party_oeid != None:
            gql_variable = variable.UpdatePartyElectionVariable(
                votes_obtained_number     = f'{tks}',
                first_obtained_number     = f'{tksRate1}%',
                second_obtained_number    = f'{tksRate2}%',
                seats                     = f'{seats}',
                id                        = party_oeid
            ).to_json()
            result = gql_update(gql_endpoint, query.gql_update_party, gql_variable)
            show_update_party(result)
    
    ### Add term office
    role, organization, term_office = '立委', '立法院', variable.termOffice_legislator_2024
    organization_id = organizations_table[organization]
    if gen_term_office==True:
        for party in patyInfo:
            patyNo    = party.get('patyNo', None)
            candInfo  = party.get('candInfo', [])
            party_oid = mapping_party_oid.get(str(patyNo), None)
            for cand in candInfo:
                candNo    = cand.get('candNo', None)
                is_victor = (cand.get('victor', '')=='*') or (cand.get('victor', '')=='!')
                if candNo!=None and is_victor==True:
                    person_info = mapping_person.get(party_oid, {}).get(candNo, {})
                    if person_info:
                        person_id   = person_info.get('person_id', None)
                        election_id = person_info.get('election_id', None)
                        if person_id and election_id:
                            gql_varible = variable.CreatePersonOrganizationVariable(
                                person_id       = person_id,
                                organization_id = organization_id,
                                election_id     = election_id,
                                role   = role,
                                source = '中選會',
                                term_office = term_office
                            ).to_json()
                            result = gql_update(gql_endpoint, query.gql_create_personOrganization, gql_varible)
                            show_create_personOrganization(result)
                    else:
                        print(f'Missing person_info for party_id: {party_oid}, order: {candNo}')
    return True

def update_normal_election(year: str, gen_term_office: bool=False):
    '''
        Give the year of election, and update the normal election result into WHORU database
    '''
    v2_districts = hp.v2_electionDistricts
    gql_normal = gql_fetch(gql_endpoint, query.get_normal_string(year))
    mapping_normal_eid = create_normal_eid(gql_normal)

    ### Get the organization informations
    gql_organizations = gql_fetch(gql_endpoint, query.gql_organizations_string)
    organizations_table = {data['name']: data['id'] for data in gql_organizations['organizations']}

    for county_code, county_name in v2_districts.items():
        v2_url = f'https://{BUCKET}/{ENV_FOLDER}/v2/{year}/legislator/district/{county_name}.json'
        raw_data = request_url(v2_url)
        if raw_data==None:
            print(f"Can't get district v2 {county_name}.json")
            continue
        v2_districts = raw_data['districts']

        for district in v2_districts:
            area_code  = district['districtName']
            candidates = district['candidates']
            for candidate in candidates:
                candNo      = candidate['candNo']
                tks         = candidate['tks']
                tksRate     = candidate['tksRate']
                candVictor  = (candidate['candVictor']==True)
                candInfo    = mapping_normal_eid.get(county_code, {}).get(area_code.zfill(2), {}).get(str(candNo), {})
                election_id = candInfo.get('election_id', None)
                person_id   = candInfo.get('person_id', None)
                if election_id != None:
                    gql_variable = variable.UpdatePersonElectionVariable(
                        votes_obtained_number     = f'{tks}',
                        votes_obtained_percentage = f'{tksRate}%',
                        elected                   = candVictor,
                        id                        = election_id
                    ).to_json()
                    result = gql_update(gql_endpoint, query.gql_update_person, gql_variable)
                    show_update_person(result, 'normal')

                if candVictor==True and gen_term_office==True and election_id!=None and person_id!=None:
                    role, organization, term_office = '立委', '立法院', variable.termOffice_legislator_2024
                    organization_id = organizations_table[organization]
                    gql_varible = variable.CreatePersonOrganizationVariable(
                        person_id = person_id,
                        organization_id = organization_id,
                        election_id = election_id,
                        role = role,
                        source = '中選會',
                        term_office = term_office
                    ).to_json()
                    result = gql_update(gql_endpoint, query.gql_create_personOrganization, gql_varible)
                    show_create_personOrganization(result)
    return True

'''
    Some tool functions will help you organize or display the data
'''
def create_normal_eid(gql_constituency):
    '''
        Create mapping_normal_eid, which shows the hierarchy from city_code to candidates.
        eid means election_id.
        <Example>
            mapping_normal_eid = {
                '68000': {               => First level:  cityCode(countyCode) [string]
                    '01': {              => Second level: areaCode [string]
                        '1': election_id => Third level:  candNo [string]
                    }
                    ...
                }
                ...
            }
    '''
    mapping_normal_eid = {}
    person_data = gql_constituency['personElections']
    reverse_city_mapping = { value: key for key, value in hp.mapping_city.items() }
    pattern = r'\d+'  ###用來找選區編號
    for data in person_data:
        electionId = data['id']
        personId   = data['person_id']['id']
        candNo     = data['number']
        city_code   = reverse_city_mapping[data['electoral_district']['city']]
        area_code   = re.findall(pattern, data['electoral_district']['name'])[0]

        subCity = mapping_normal_eid.setdefault(city_code, {})
        subArea = subCity.setdefault(area_code, {})
        subArea[candNo] = {
            'election_id': electionId,
            'person_id': personId
        }
    return mapping_normal_eid

def show_update_person(result, election_type:str):
    if result:
        result  = result['item']
        id      = result['id']
        tks     = result['votes_obtained_number']
        tksRate = result['votes_obtained_percentage']
        elected = result['elected']
        print(f'Update {election_type} person id={id} to tks={tks}, tksRate={tksRate}, and elected={elected}')

def show_update_party(result):
    if result:
        result   = result['item']
        id       = result['id']
        tks      = result['votes_obtained_number']
        tksRate1 = result['first_obtained_number']
        tksRate2 = result['second_obtained_number']
        seats = result['seats']
        print(f'Update election party id={id} to tks={tks}, tksRate1={tksRate1}, tksRate2={tksRate2}, and seats={seats}')

def show_create_personOrganization(result):
    if result:
        result   = result['item']
        personOrganization_id = result['id']
        print(f'Successfully create personOrganization with id={personOrganization_id}')