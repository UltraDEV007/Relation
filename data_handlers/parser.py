from datetime import datetime
import data_handlers.helpers as hp

def parse_county(data, election_type, helper=hp.helper):
    '''
        Parse the raw data into two level(county, town).
    '''
    ### Initialize data
    preprocessing_result = {}
    updatedAt = datetime.strptime(data[helper['START_TIME']], '%m%d%H%M')
    updatedAt = f"{datetime.now().year}-{datetime.strftime(updatedAt, '%m-%d %H:%M')}"
    preprocessing_result['updateAt'] = updatedAt
    preprocessing_result['districts'] = {}

    ### Filter the data first
    election_data    = data[helper[election_type]]

    ### Packaging the district data
    for district in election_data:
        prvCode  = district.get('prvCode',  hp.DEFAULT_PRVCODE)
        cityCode = district.get('cityCode', hp.DEFAULT_CITYCODE)
        deptCode = district.get('deptCode', hp.DEFAULT_DEPTCODE)
        profRate = district.get('profRate', hp.DEFAULT_PROFRATE)
        tboxNo   = district.get('tboxNo',   hp.DEFAULT_INT)
        
        ### Store prof3 and prof7 so that we can calculate profRate in village level
        voterTurnout   = district.get(helper['VOTER_TURNOUT'], hp.DEFAULT_INT)
        eligibleVoters = district.get(helper['ELIGIBLE_VOTERS'], hp.DEFAULT_INT) 

        ### unique key in the first level
        county_code = f"{prvCode}{cityCode}"
        
        ### 不分區立委(Party)的候選人名單是黨，需要特別處理(無論是黨或人，在前處理的過程中一律轉為candTksInfo)
        if election_type == 'party':
            raw_candidates = district.get('patyTksInfo', None)
        else:
            raw_candidates = district.get('candTksInfo', None)

        ### store data
        subLevel = preprocessing_result['districts'].setdefault(county_code, [])
        deptInfo = {
            'deptCode': deptCode,
            'profRate': profRate,
            'tboxNo':   tboxNo,
            'voterTurnout': voterTurnout,
            'eligibleVoters': eligibleVoters,
            'candTksInfo': raw_candidates
        }
        subLevel.append(deptInfo)
    return preprocessing_result

def parse_town(county_code, county_data):
    '''
        Parse the data into level (town, villages)
    '''
    preprocessing_result = {}
    preprocessing_result['towns'] = {}
    preprocessing_result['county_code'] = county_code

    for data in county_data:
        deptCode = data.get('deptCode', hp.DEFAULT_DEPTCODE)
        profRate = data.get('profRate', hp.DEFAULT_PROFRATE)
        tboxNo   = data.get('tboxNo',   hp.DEFAULT_INT)
        
        ### Store voterTurnout and eligibleVoters so that we can calculate profRate in village level
        voterTurnout   = data.get('voterTurnout', hp.DEFAULT_INT)
        eligibleVoters = data.get('eligibleVoters', hp.DEFAULT_INT) 

        subLevel = preprocessing_result['towns'].setdefault(deptCode, [])
        villInfo = {
            'tboxNo': tboxNo,
            'profRate': profRate,
            'voterTurnout': voterTurnout,
            'eligibleVoters': eligibleVoters,
            'candTksInfo': data.get('candTksInfo', None)
        }
        subLevel.append(villInfo)
    return preprocessing_result

def parse_constituency_area(data, helper=hp.helper):
    '''
        Parse the raw data into two level(county, town).
    '''
    ### Initialize data
    preprocessing_result = {}
    updatedAt = datetime.strptime(data[helper['START_TIME']], '%m%d%H%M')
    updatedAt = f"{datetime.now().year}-{datetime.strftime(updatedAt, '%m-%d %H:%M')}"
    preprocessing_result['updateAt'] = updatedAt
    preprocessing_result['districts'] = {}

    ### Filter the data first
    president_data    = data[helper['LOCAL_LEGISLATOR']]

    ### Packaging the district data
    for district in president_data:
        prvCode  = district.get('prvCode',  hp.DEFAULT_PRVCODE)
        cityCode = district.get('cityCode', hp.DEFAULT_CITYCODE)
        areaCode = district.get('areaCode', hp.DEFAULT_AREACODE)
        deptCode = district.get('deptCode', hp.DEFAULT_DEPTCODE)
        profRate = district.get('profRate', hp.DEFAULT_PROFRATE)
        tboxNo   = district.get('tboxNo',   hp.DEFAULT_INT)
        
        ### Store prof3 and prof7 so that we can calculate profRate in village level
        voterTurnout   = district.get(helper['VOTER_TURNOUT'], hp.DEFAULT_INT)
        eligibleVoters = district.get(helper['ELIGIBLE_VOTERS'], hp.DEFAULT_INT) 

        ### unique key in the first level
        county_code = f"{prvCode}{cityCode}"

        ### store data
        subLevel = preprocessing_result['districts'].setdefault(f'{county_code}{areaCode}', [])
        areaInfo = {
            'deptCode': deptCode,
            'areaCode': areaCode,
            'profRate': profRate,
            'tboxNo':   tboxNo,
            'voterTurnout': voterTurnout,
            'eligibleVoters': eligibleVoters,
            'candTksInfo': district.get('candTksInfo', None)
        }
        subLevel.append(areaInfo)
    return preprocessing_result

def parse_seat(data, mapping_party_seat):
    '''
    Description:
        從final_A.json資料當中抓出各政黨的不分區立委中選席次，並將其寫入到不分區政黨對照表中
    Input:
        data - final_A.json
    '''
    seat_data = data['M4']
    patyInfo  = seat_data.get('patyInfo', 0)
    for info in patyInfo:
        patyNo    = info.get('patyNo', None)
        seatCount = info.get('victorMarkCount', None)
        if patyNo:
            party = mapping_party_seat.get(str(patyNo), None)
            if party:
                party['seat'] = seatCount
    return "ok"