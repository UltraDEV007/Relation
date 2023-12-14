'''
    helpers is a tool that content structure which you can use to help mapping the
    column name in the raw cec data.
    Besides, we provide DEFAULT_VALUE for each type of data. 
'''

helpers = {
    '2024':{
        'START_TIME': 'ST',
        ### For running.json and final.json
        'PRESIDENT': 'P1',
        'LOCAL_LEGISLATOR': 'L1',
        'PLAIN_INDIGENOUS_LEGISLATOR': 'L2',
        'MOUNTAIN_INDIGENOUS_LEGISLATOR': 'L3',
        'PARTY_LEGISLATOR': 'L4',
        
        ### For final_A.json
        'PARTY_QUOTA': 'M4',
        'ELECTED_ANALYSIS': 'AL',
        
        ### For detail data
        'VOTER_TURNOUT'  : 'prof3',
        'ELIGIBLE_VOTERS': 'prof7',
        'TOWN': 'deptCode', 
        'PROFRATE': 'profRate',
        'CANDIDATES': 'candTksInfo',
        
        ### Candidate ID mapping for presidents
        'CAND_PRESIDENT_MAPPING': {
            1: {
                "name": "柯文哲 吳欣盈",
                "party": "台灣民眾黨"
            },
            2: {
                "name": "賴清德 蕭美琴",
                "party": "民主進步黨"
            },
            3: {
                "name": "侯友宜 趙少康",
                "party": "中國國民黨"
            }
        },
    }
}
helper = helpers['2024']
helper['MAX_CAND_NUMBER'] = max(helper['CAND_PRESIDENT_MAPPING'].keys())

DEFAULT_PRVCODE     = '00'
DEFAULT_CITYCODE    = '000'
DEFAULT_DEPTCODE    = '000'
DEFAULT_FLOAT = DEFAULT_PROFRATE = 0.0
DEFAULT_LIST  = DEFAULT_CANDTKSINFO = []
DEFAULT_INT   = 0

UNKNOWN_CANDIDATE = {
    "name": "未知",
    "party": "未知黨"
}