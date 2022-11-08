from  councilMember import gen_vote
from tools.query import query_elections, query_personElections_councilMember
from configs import election_types
import json

def vote():
    election_type = '縣市議員'
    all_elections = query_elections(election_type)
    election_type = election_types.get(election_type)
    print(all_elections)
    for year in all_elections:
        print(year)
        if year == 2022:
            continue
        election = all_elections[year]
        election_query_script = ','.join(
            ['{id:{equals:%s}}' % electionId for electionId in election])
        personElections_data = query_personElections_councilMember(election_query_script)
        for county_code in personElections_data.keys():
            print(county_code)
            gen_vote(county_code, personElections_data, year, personElections_data)
if __name__ == '__main__':
    vote()

