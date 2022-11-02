from tools.conn import gql_client
from gql import gql


def query_elections(electioin_type):
    query = '''
    query{
    elections(where:{type:{in:"%s"}}, orderBy:{ election_year_year:desc}){
        id
        name
        election_year_year
    }
    }''' % electioin_type
    client = gql_client()
    r = client.execute(gql(query))
    if r['elections']:
        result = {}
        for election in r['elections']:
            if election['election_year_year'] in result:
                result[election['election_year_year']].append(election['id'])
            else:
                result[election['election_year_year']] = [election['id']]
        return result


def query_personElections(electionID, district=''):
    query = '''
            query{
            personElections(where:{election:{OR:[%s]}%s}, orderBy:{number:asc}){
            id
            number
            votes_obtained_number
            votes_obtained_percentage
            elected
            electoral_district{
                name
                indigenous
                city
            }
            person_id{
                id
                name
                image
            }
            party{
                id
                name
                image
            }
            election{
                id
            }
            }
        }''' % (electionID, district)
    client = gql_client()
    # print(query)
    r = client.execute(gql(query))
    return r['personElections']