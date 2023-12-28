special_municipality =  {
                "臺北市": "",
                "新北市": "",
                "桃園市": "",
                "臺中市": "",
                "臺南市": "",
                "高雄市": ""}  
default_special_municipality = {
    "63_000_000": [6, 8, 12], # default(before start) showing candidateNo
    "65_000_000": [1, 2],
    "68_000_000": [1, 3, 4],
    "66_000_000": [1, 2, 3],
    "67_000_000": [2, 3, 5],
    "64_000_000": [1, 3, 4],
}
default_tv = {
    "63_000_000": [6, 8, 12], # default(before start) showing candidateNo
    "65_000_000": [1, 2],
    "68_000_000": [1, 3],
    "66_000_000": [2, 3],
    "67_000_000": [3, 5],
    "64_000_000": [3, 4],
}
default_seat = {
    "63_000_000": 61,
    "65_000_000": 66,
    "68_000_000": 63,
    "66_000_000": 65,
    "67_000_000": 57,
    "64_000_000": 65,
    "10_002_000": 34,
    "10_004_000": 37,
    "10_005_000": 38,
    "10_007_000": 54,
    "10_008_000": 37,
    "10_009_000": 43,
    "10_010_000": 37,
    "10_013_000": 55,
    "10_015_000": 33,
    "10_014_000": 30,
    "10_016_000": 19,
    "10_017_000": 31,
    "10_018_000": 34,
    "10_020_000": 23,
    "09_020_000": 19,
    "09_007_000": 9
}
default_seat_name = "開票中 席次尚未確認"

districts_mapping = {"臺北市": "taipeiCity", "新北市": "newTaipeiCity", "桃園市": "taoyuanCity", "臺中市": "taichungCity", "臺南市": "tainanCity", "高雄市": "kaohsiungCity",
                     "新竹縣": "hsinchuCounty", "苗栗縣": "miaoliCounty", "彰化縣": "changhuaCounty", "南投縣": "nantouCounty", "雲林縣": "yunlinCounty", "嘉義縣": "chiayiCounty",
                     "屏東縣": "pingtungCounty", "宜蘭縣": "yilanCounty", "花蓮縣": "hualienCounty", "臺東縣": "taitungCounty", "澎湖縣": "penghuCounty", "金門縣": "kinmenCounty",
                     "連江縣": "lienchiangCounty", "基隆市": "keelungCity", "新竹市": "hsinchuCity", "嘉義市": "chiayiCity", "桃園縣": "taoyuanCounty", "臺中縣": "taichungCounty", "臺北縣": "taipeiCounty", "高雄縣": "kaohsiungCounty", "臺南縣": "tainanCounty"}
election_types = {'省長': 'governorProvince', '省議員': 'provinceCouncilMember', '縣市首長': 'mayor', '縣市議員': 'councilMember', '立法委員': 'legislator',
                  '國大代表': 'nationalAssembly', '總統': 'president', '鄉鎮市區長': 'townMayor', '市/區民代表': 'townCouncilMember', '村里長': 'villageRepresentative', }
upload_configs = {
                  "real_time": "no-store",
                  "cache_control_short": 'max-age=30',
                  "cache_control": 'max-age=86400',
                  "content_type_json": 'application/json',
                  }