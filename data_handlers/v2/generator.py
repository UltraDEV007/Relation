from datetime import datetime
import data_handlers.helpers as hp
import data_handlers.templates as tp
import data_handlers.v2.converter as converter

from data_handlers.helpers import helper

def search_constituency_candidate(countyCode:str, areaCode: str, candNo: int):
    candInfo = hp.mapping_constituency_cand.get(countyCode,{}).get(areaCode,{}).get(candNo, None)
    return candInfo

def generate_v2_president(raw_data, mapping_json, year: str):
    election_type = 'president'
    election_data = raw_data[helper['president']]

    updatedAt = datetime.strptime(raw_data[helper['START_TIME']], '%m%d%H%M%S')
    updatedAt = f"{datetime.now().year}-{datetime.strftime(updatedAt, '%m-%d %H:%M:%S')}"

    v2Template = tp.V2Template(
        updatedAt = updatedAt,
        year      = year,
        type      = election_type,
        title     = '正副總統選舉',
        version   = 'v2'
    ).to_json()

    for data in election_data:
        prvCode = data.get('prvCode', hp.DEFAULT_PRVCODE)
        cityCode = data.get('cityCode', hp.DEFAULT_CITYCODE)
        countyCode = f'{prvCode}{cityCode}'
        if countyCode == hp.COUNTRY_CODE:
            raw_candidates = data.get('candTksInfo', [])
            candidates = converter.convert_v2_president_candidates(raw_candidates, mapping_json)
            v2Template['candidates'] = candidates
            break
    return v2Template

def generate_v2_special_legislator(raw_data, election_type, mapping_json, year: str):
    '''
        election_type = 'legislator-mountainIndigenous' / 'legislator-plainIndigenous'
        mapping_json  = mapping candidates json 
    '''
    election_data = raw_data[helper[election_type]]

    updatedAt = datetime.strptime(raw_data[helper['START_TIME']], '%m%d%H%M%S')
    updatedAt = f"{datetime.now().year}-{datetime.strftime(updatedAt, '%m-%d %H:%M:%S')}"
    
    v2Template = tp.V2Template(
        updatedAt = updatedAt,
        year      = year,
        type      = election_type,
        title     = '立法委員選舉（原住民）',
        version   = 'v2'
    ).to_json()

    for data in election_data:
        prvCode = data.get('prvCode', hp.DEFAULT_PRVCODE)
        cityCode = data.get('cityCode', hp.DEFAULT_CITYCODE)
        countyCode = f'{prvCode}{cityCode}'
        if countyCode == hp.COUNTRY_CODE:
            raw_candidates = data.get('candTksInfo', [])
            candidates = converter.convert_v2_person_candidates(raw_candidates, mapping_json)
            v2Template['candidates'] = candidates
            break
    return v2Template

def generate_v2_party_legislator(raw_data, mapping_json, year: str):
    election_type = 'legislator-party'
    election_data = raw_data[helper[election_type]]

    updatedAt = datetime.strptime(raw_data[helper['START_TIME']], '%m%d%H%M%S')
    updatedAt = f"{datetime.now().year}-{datetime.strftime(updatedAt, '%m-%d %H:%M:%S')}"
    
    v2Template = tp.V2Template(
        updatedAt = updatedAt,
        year     = year,
        type     = election_type,
        title    = '立法委員選舉（不分區）',
        version  = 'v2'
    ).to_json()

    for data in election_data:
        prvCode = data.get('prvCode', hp.DEFAULT_PRVCODE)
        cityCode = data.get('cityCode', hp.DEFAULT_CITYCODE)
        countyCode = f'{prvCode}{cityCode}'
        if countyCode == hp.COUNTRY_CODE:
            raw_candidates = data.get('patyTksInfo', [])
            candidates = converter.convert_v2_party_candidates(raw_candidates, mapping_json)
            v2Template['parties'] = candidates
            break
    return v2Template

def generate_v2_district_legislator(raw_data, year: str):
    '''
    Description:
        在區域立委中會產出各縣市的json檔案，這個函式最後會回傳的不是單份json，而是檔案名稱與資料的字典。
    Output:
        district_name - {filename, data}
        <Example>
            {
                'changhuaCounty.json': DATA,
                'hsinchuCity.json': DATA,
                ...
            }
    '''
    result = {}
    election_type = 'legislator-district'
    election_data = raw_data[helper[election_type]]
    districts_list = list(hp.v2_electionDistricts.keys())

    updatedAt = datetime.strptime(raw_data[helper['START_TIME']], '%m%d%H%M%S')
    updatedAt = f"{datetime.now().year}-{datetime.strftime(updatedAt, '%m-%d %H:%M:%S')}"

    ### categorize the data into hierarchy, county_code->area_code->candNo
    hierarchy = {}
    for data in election_data:
        prvCode = data.get('prvCode', hp.DEFAULT_PRVCODE)
        cityCode = data.get('cityCode', hp.DEFAULT_CITYCODE)
        areaCode = data.get('areaCode', hp.DEFAULT_AREACODE)
        if areaCode == hp.DEFAULT_AREACODE:
            continue
        
        countyCode = f'{prvCode}{cityCode}' ### include city and county
        if countyCode in districts_list:
            raw_candidates = data.get('candTksInfo', [])
            subCounty = hierarchy.setdefault(countyCode, {})
            subArea   = subCounty.setdefault(areaCode, {})

            for candidate in raw_candidates:
                candNo = candidate.get('candNo', hp.DEFAULT_INT)
                cand_info = subArea.get(str(candNo), None)
                if cand_info:
                    cand_info['tks'] += candidate['tks']
                else:
                    candidate['candVictor'] = False ### No victor yet
                    candidate['tksRate'] = hp.DEFAULT_FLOAT
                    subArea[str(candNo)] = candidate
    
    ### use the hierarchy to create the county.json
    for countyCode, countyData in hierarchy.items():
        city = hp.mapping_city.get(countyCode, 'Unknown')
        city_v2 = hp.v2_electionDistricts.get(countyCode, None)
        if city_v2 == None:
            continue
        v2_template =  tp.V2Template(
            updatedAt = updatedAt,
            year      = year,
            type      = election_type,
            title     = f"立法委員選舉（{city}）",
            version   = 'v2'
        ).to_json()
        for areaCode, areaData in countyData.items():
            v2_area_template = tp.V2ConstituencyAreaTemplate(
                districtName = areaCode.zfill(2) ###補齊兩位數選區字串
            ).to_json()
            ### calculate the winner and tksRate in the same area
            winner  = list(areaData.keys())[0]
            max_tks, total_tks = 0, 0
            for candNo, candData in areaData.items():
                tks = candData['tks']
                if tks > max_tks:
                    max_tks, winner = tks, candNo
                total_tks += tks
            areaData[winner]['candVictor'] = True
            
            for candNo, candData in areaData.items():
                tks = candData.get('tks', hp.DEFAULT_INT)
                candVictor = candData.get('candVictor', False)
                person_template = tp.V2PersonCandidateTemplate(
                    candNo     = int(candNo),
                    tks        = tks,
                    candVictor = candVictor,
                    tksRate    = round((tks/total_tks)*100, hp.ROUND_DECIMAL) if total_tks!=0 else 0
                ).to_json()
                
                candInfo = search_constituency_candidate(countyCode, areaCode, int(candNo))
                if candInfo:
                    person_template['name'] = candInfo.get('person', None)
                    person_template['party'] = candInfo.get('party', None)
                
                v2_area_template['candidates'].append(person_template)
            v2_template['districts'].append(v2_area_template)
        result[f'{city_v2}.json'] = v2_template
    return result