import os
from tools.uploadGCS import open_file

'''
    helpers is a tool that content structure which you can use to help mapping the
    column name in the raw cec data.
    Besides, we provide DEFAULT_VALUE for each type of data. 
'''

'''
LEGISLATOR: 立委
PLAIN: 平地
PARTY: 不分區
QUOTA: 名額(PARTY_QUOTA指的是不分區配額)
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

COUNTRY_CODE = '00000'    ### 全國代碼
FUJIAN_PRV_CODE = '09000' ### 福建省省碼

DEFAULT_CANDVICTOR = ' '  ### Empty string with len=1
DEFAULT_PRVCODE = '00'
DEFAULT_CITYCODE = '000'
DEFAULT_DEPTCODE = DEFAULT_TOWNCODE = DEFAULT_VILLCODE = '000'
DEFAULT_FLOAT = DEFAULT_PROFRATE = 0.0
DEFAULT_LIST  = DEFAULT_CANDTKSINFO = []
DEFAULT_INT   = 0
ROUND_DECIMAL = 2

UNKNOWN_CANDIDATE = {
    "name": "未知",
    "party": "未知黨"
}

### 首都(Municipality)列表
MUNICIPALITY = [
    '臺北市', '新北市', '桃園市', '臺中市', '臺南市', '高雄市'
]

### Mapping files: Loading mapping files
### TODO: Remove some unnecessary files and refactor 'year'
def reverse_mapping(data):
    result = {}
    for key, value in data.items():
        result[value] = key
    return result
root = os.path.join('mapping', '2024')

path = os.path.join(root, 'mapping_city.json')
mapping_city = open_file(path)

path = os.path.join(root, 'mapping_town.json')
mapping_town = open_file(path)

path = os.path.join(root, 'mapping_vill.json')
mapping_vill = open_file(path)

path = os.path.join(root, 'mapping_vill_code.json')
mapping_vill_code = open_file(path)

path = os.path.join(root, 'mapping_code_vill.json')
mapping_code_vill = open_file(path)

path = os.path.join(root, 'mapping_president.json')
mapping_president = open_file(path)

path = os.path.join(root, 'mapping_tboxNo_vill.json')
mapping_tboxno_vill = open_file(path)

### Reverse mapping
reverse_mapping_town = reverse_mapping(mapping_town)