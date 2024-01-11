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

helper = {
        'START_TIME': 'ST',
        ### For running.json and final.json
        'PRESIDENT': 'P1',
        'LOCAL_LEGISLATOR': 'L1',                 #區域立委(選人)
        'PLAIN_INDIGENOUS_LEGISLATOR': 'L2',      #平地原住民立委(選人)
        'MOUNTAIN_INDIGENOUS_LEGISLATOR': 'L3',   #山地原住民立委(選人)
        'PARTY_LEGISLATOR': 'L4',                 #不分區立委(選黨)
        
        ### For v2
        'president': 'P1',
        'legislator-district': 'L1',
        'legislator-plainIndigenous': 'L2',
        'legislator-mountainIndigenous': 'L3',
        'legislator-party': 'L4',
        'WHORU_WEBSITE_PERSON': 'https://whoareyou.readr.tw/person/',

        ### For seats calculation
        'normal': 'L1',
        'plain-indigenous': 'L2',
        'mountain-indigenous': 'L3',
        'party': 'L4',
    
        'plain-indigenous-allseats': 3,
        'mountain-indigenous-allseats': 3,
        'normal-allseats': 73, ### TODO: NEED TO MODIFY
        'party-allseats': 34,
        'all-allseats': 113,
        
        ### 立委資料的統一格式字串及較簡易的KEY
        'plain': 'L2',
        'plainIndigenous': 'L2',
        'mountain': 'L3',
        'mountainIndigenous': 'L3',
        'party': 'L4',
        
        ### For final_A.json
        'PARTY_QUOTA': 'M4',
        'ELECTED_ANALYSIS': 'AL',
        
        ### For detail data
        'VOTER_TURNOUT'  : 'prof3',
        'ELIGIBLE_VOTERS': 'prof7',
        'TOWN': 'deptCode', 
        'PROFRATE': 'profRate',
        'CANDIDATES': 'candTksInfo',
}

COUNTRY_CODE    = '00000' ## 國碼
TAIWAN_PRV_CODE = '10000' ## 台灣省省碼
FUJIAN_PRV_CODE = '09000' ## 福建省省碼
COUNTY_CODE_LENGTH = len(COUNTRY_CODE)
NO_PROCESSING_CODE = [COUNTRY_CODE, TAIWAN_PRV_CODE, FUJIAN_PRV_CODE]

DEFAULT_PRVCODE = DEFAULT_AREACODE = '00'
DEFAULT_CITYCODE = '000'
DEFAULT_DEPTCODE = DEFAULT_TOWNCODE = DEFAULT_VILLCODE = '000'
DEFAULT_FLOAT = DEFAULT_PROFRATE = 0.0
DEFAULT_LIST  = DEFAULT_CANDTKSINFO = []
DEFAULT_INT   = 0
ROUND_DECIMAL = 2


INDEPENDENT_PARTY = "無黨籍及未經政黨推薦"
V2_INDEPENDENT_PARTY = "無黨籍"
UNDETERMINED_INFO = "席次尚未確認"

UNKNOWN_CAND_NAME = "未知參選人"
UNKNOWN_CANDIDATE = {
    "name": "未知參選人",
    "party": "未知政黨"
}

UNKNOWN_PARTY = {
    "name": "未知參選人" ,
    "seat": DEFAULT_INT
}

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

### 立委相關的對照表
path = os.path.join(root, 'mapping_mountain_cand.json')
mapping_mountain_cand = open_file(path)

path = os.path.join(root, 'mapping_plain_cand.json')
mapping_plain_cand = open_file(path)

path = os.path.join(root, 'mapping_constituency_cand.json')
mapping_constituency_cand = open_file(path)

path = os.path.join(root, 'mapping_party_seat.json')
mapping_party_seat_init = open_file(path) ### Used to initialize the seat data
mapping_party_seat = open_file(path)

path = os.path.join(root, 'mapping_nickname.json')
mapping_nickname = open_file(path) ### Mapping relationship: [areaCode, nickname]

### V2地區英文名稱對照表
path = os.path.join(root, 'v2_electionDistricts.json')
v2_electionDistricts = open_file(path)

### Reverse mapping
reverse_mapping_town = reverse_mapping(mapping_town)