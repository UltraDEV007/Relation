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


districts_mapping = {"臺北市": "taipeiCity", "新北市": "newTaipeiCity", "桃園市": "taoyuanCity", "臺中市": "taichungCity", "臺南市": "tainanCity", "高雄市": "kaohsiungCity",
                     "新竹縣": "hsinchuCounty", "苗栗縣": "miaoliCounty", "彰化縣": "changhuaCounty", "南投縣": "nantouCounty", "雲林縣": "yunlinCounty", "嘉義縣": "chiayiCounty",
                     "屏東縣": "pingtungCounty", "宜蘭縣": "yilanCounty", "花蓮縣": "hualienCounty", "臺東縣": "taitungCounty", "澎湖縣": "penghuCounty", "金門縣": "kinmenCounty",
                     "連江縣": "lienchiangCounty", "基隆市": "keelungCity", "新竹市": "hsinchuCity", "嘉義市": "chiayiCity", "桃園縣": "taoyuanCounty", "臺中縣": "taichungCounty", "臺北縣": "taipeiCounty", "高雄縣": "kaohsiungCounty", "臺南縣": "tainanCounty"}
election_types = {'省長': 'governorProvince', '省議員': 'provinceCouncilMember', '縣市首長': 'mayor', '縣市議員': 'councilMember', '立法委員': 'legislator',
                  '國大代表': 'nationalAssembly', '總統': 'president', '鄉鎮市區長': 'townMayor', '市/區民代表': 'townCouncilMember', '村里長': 'villageRepresentative', }
upload_configs = {"bucket_name": 'whoareyou-gcs.readr.tw',
                  "cache_control_short": 'max-age=30',
                  "cache_control": 'max-age=86400',
                  "content_type_json": 'application/json',
                  }