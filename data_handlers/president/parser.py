from datetime import datetime
from data_handlers.helpers import helpers
import data_handlers.helpers as hp

def parse_county(data, helper=helpers['2024']):
    '''
        Parse the raw data into two level(county, town).
    '''
    ### Initialize data
    parse_result = {}
    updatedAt = datetime.strptime(data[helper['START_TIME']], '%m%d%H%M%S')
    updatedAt = f"{datetime.now().year}-{datetime.strftime(updatedAt, '%m-%d %H:%M:%S')}"
    parse_result['updateAt'] = updatedAt
    parse_result['districts'] = {}

    ### Filter the data first
    president_data    = data[helper['PRESIDENT']]

    ### Packaging the district data
    for district in president_data:
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

        ### store data
        subLevel = parse_result['districts'].setdefault(county_code, [])
        deptInfo = {
            'deptCode': deptCode,
            'profRate': profRate,
            'tboxNo':   tboxNo,
            'voterTurnout': voterTurnout,
            'eligibleVoters': eligibleVoters,
            'candTksInfo': district.get('candTksInfo', None)
        }
        subLevel.append(deptInfo)
    return parse_result

def parse_town(county_code, county_data):
    '''
        Parse the data into level (town, villages)
    '''
    parse_result = {}
    parse_result['towns'] = {}
    parse_result['county_code'] = county_code

    for data in county_data:
        deptCode = data.get('deptCode', hp.DEFAULT_DEPTCODE)
        profRate = data.get('profRate', hp.DEFAULT_PROFRATE)
        tboxNo   = data.get('tboxNo',   hp.DEFAULT_INT)
        
        ### Store voterTurnout and eligibleVoters so that we can calculate profRate in village level
        voterTurnout   = data.get('voterTurnout', hp.DEFAULT_INT)
        eligibleVoters = data.get('eligibleVoters', hp.DEFAULT_INT) 

        subLevel = parse_result['towns'].setdefault(deptCode, [])
        villInfo = {
            'tboxNo': tboxNo,
            'profRate': profRate,
            'voterTurnout': voterTurnout,
            'eligibleVoters': eligibleVoters,
            'candTksInfo': data.get('candTksInfo', None)
        }
        subLevel.append(villInfo)
    return parse_result