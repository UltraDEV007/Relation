import data_handlers.helpers as hp
import data_handlers.templates as tp
import data_handlers.v2.converter as converter

from data_handlers.helpers import helper

def generate_v2_president(raw_data, mapping_json, year: str):
    election_type = 'president'
    election_data = raw_data[helper['president']]
    v2Template = tp.V2Template(
        updateAt = raw_data[helper['START_TIME']],
        year     = year,
        type     = election_type,
        title    = '正副總統選舉',
        version  = 'v2'
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