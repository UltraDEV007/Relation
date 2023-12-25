
import data_handlers.helpers as hp
import data_handlers.templates as tp

def convert_v2_president_candidates(raw_candidates, mapping_json):
    result = []
    for candidate in raw_candidates:
        candidateTemplate = tp.PersonCandidateTemplate(
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
        candidateTemplate['name'].append(president['person'])
        candidateTemplate['name'].append(vice['person'])
        candidateTemplate['party'].append(president['party'])

        ### If the party of president and vice are different, append the party of vice
        party_first = president['party'].get('id', '')
        party_second = vice['party'].get('id', '')
        if party_first!=party_second:
            candidateTemplate['party'].append(vice['party'])

        result.append(candidateTemplate)
    return result