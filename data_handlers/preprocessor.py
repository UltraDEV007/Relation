from datetime import datetime
from helpers import helpers

import data_handlers.helpers as hp
from data_handlers.helpers import helpers

def parse_president_cec(data, helper=helpers['2024']):
    '''
        In this function, we'll organize the district data into different level(county, town).
    '''
    ### Initialize data
    preprocessing_result = {}
    updatedAt = datetime.strptime(data[helper['START_TIME']], '%m%d%H%M%S')
    updatedAt = f"{datetime.now().year}-{datetime.strftime(updatedAt, '%m-%d %H:%M:%S')}"
    preprocessing_result['updateAt'] = updatedAt
    preprocessing_result['districts'] = {}
    
    ### Filter the data first
    president_data    = data[helper['PRESIDENT']] 

    ### Packaging the district data
    for district in president_data:
        prvCode  = district.get('prvCode',  hp.DEFAULT_PRVCODE)
        cityCode = district.get('cityCode', hp.DEFAULT_CITYCODE)
        deptCode = district.get('deptCode', hp.DEFAULT_DEPTCODE)
        profRate = district.get('profRate', hp.DEFAULT_PROFRATE)
        votersTurnout  = district.get(helper['VOTER_TURNOUT'], hp.DEFAULT_INT)
        eligibleVoters = district.get(helper['ELIGIBLE_VOTERS'], hp.DEFAULT_INT)
        
        ### unique key in the first level
        county_code = f"{prvCode}{cityCode}"
        
        ### store data
        subLevel = preprocessing_result['districts'].setdefault(county_code, [])
        deptInfo = {
            'deptCode': deptCode,
            'profRate': profRate,
            'votersTurnout':  votersTurnout,
            'eligibleVoters': eligibleVoters,
            'candTksInfo': district.get('candTksInfo', None)
        }
        subLevel.append(deptInfo)
    return preprocessing_result