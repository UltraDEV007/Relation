from  mayor import gen_vote
from tools.query import query_elections, query_personElections_mayor
from configs import election_types
import json

def vote():
    election_type = '縣市首長'
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
        personElections_data = query_personElections_mayor(election_query_script)
        
        gen_vote(personElections_data, personElections_data, year)
if __name__ == '__main__':
    vote()
    print("done")

