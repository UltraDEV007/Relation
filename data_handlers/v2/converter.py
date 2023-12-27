import data_handlers.helpers as hp
import data_handlers.templates as tp
from data_handlers.helpers import helper

def convert_v2_president_candidates(raw_candidates, mapping_json):
    '''
    Description: 
        Convert the raw candidate info of president. You need to merge the information of
        president and vice.
    '''
    result = []
    whoru_person = helper['WHORU_WEBSITE_PERSON']
    for candidate in raw_candidates:
        candidateTemplate = tp.PresidentCandidateTemplate(
            tks = candidate.get('tks', hp.DEFAULT_INT),
            tksRate = candidate.get('tksRate', hp.DEFAULT_FLOAT),
            candVictor = True if (candidate.get('candVictor')=='*') else False,
        ).to_json()
        candNo = candidate.get('candNo', hp.DEFAULT_INT)
        
        candInfo = mapping_json.get(str(candNo), None)
        if candInfo == None:
            continue
        president = candInfo['first']
        vice      = candInfo['second']
        candidateTemplate['candNo'] = candNo

        person_id = president['person'].get('id', '')
        candidateTemplate['name'].append(        
            tp.PersonInfoTemplate(
                label  = president['person'].get('name', None),
                href   = f'{whoru_person}{person_id}',
                imgSrc = president['person'].get('image', None),
            ).to_json()
        )

        person_id = vice['person'].get('id', '')
        candidateTemplate['name'].append(
            tp.PersonInfoTemplate(
                label  = vice['person'].get('name', None),
                href   = f'{whoru_person}{person_id}',
                imgSrc = vice['person'].get('image', None),
            ).to_json()
        )

        candidateTemplate['party'].append(
            tp.PartyInfoTemplate(
                label = president['party'].get('name', None),
            ).to_json()
        )

        ### If the party of president and vice are different, append the party of vice
        party_first = president['party'].get('id', '')
        party_second = vice['party'].get('id', '')
        if party_first!=party_second:
            candidateTemplate['party'].append(
                tp.PartyInfoTemplate(
                    label = vice['party'].get('name', None),
                ).to_json()
            )
        result.append(candidateTemplate)
    return result


def convert_v2_person_candidates(raw_candidates, mapping_json):
    '''
    Description:
        Convert the raw candidates information in legislator person election
    Input:
        mapping_json - The mapping file to map candNo to the candidator data
    '''
    result = []
    website = helper['WHORU_WEBSITE_PERSON']
    for candidate in raw_candidates:
        candidateTemplate = tp.V2PersonCandidateTemplate(
            tks = candidate.get('tks', hp.DEFAULT_INT),
            tksRate = candidate.get('tksRate', hp.DEFAULT_FLOAT),
            candVictor = True if (candidate.get('candVictor')=='*') else False,
        ).to_json()
        candNo = candidate.get('candNo', hp.DEFAULT_INT)
        
        candInfo = mapping_json.get(str(candNo), None)
        if candInfo == None:
            continue
        candidateTemplate['candNo'] = candNo

        personInfo, partyInfo = candInfo['person'], candInfo['party']

        person_id = personInfo.get('id', '')
        candidateTemplate['name'] = tp.V2PersonInfoTemplate(
            label = personInfo.get('name', None), 
            href  = f'{website}{person_id}', 
            imgSrc= personInfo.get('image', None)
        ).to_json()

        if partyInfo:
            candidateTemplate['party'] = tp.V2PartyInfoTemplate(
                label = partyInfo.get('name', None),
            ).to_json()
        result.append(candidateTemplate)
    return result