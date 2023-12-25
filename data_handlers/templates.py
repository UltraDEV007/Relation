import copy

'''
Description:
    NoteTemplate is a special template to highlight some special events.
    For example, "嘉義市補選" is a special election after ending of the normal election.
    
    In this case, you should patch the information in DistrictTemplate.
    Here is the example of how you pathc the note information:
    EX: distrctTemp = DistrictTemplate().set_note(NOTE_INFORMATION).to_json()
'''
class NoteTemplate:
    def __init__(self, displayText: str='', displayVotes: bool=True):
        self.text = displayText
        self.displayVotes = displayVotes
    def to_json(self):
        return vars(self)
'''
Description
    The skeleton template of each json file. For example,
'''
class CountryTemplate:
    def __init__(self, updateAt: str='', is_running: bool=False, is_started: bool=False, summary: dict={}, districts: list=[]):
        self.updateAt   = updateAt
        self.is_running = is_running
        self.is_started = is_started
        self.summary    = copy.deepcopy(summary)
        self.districts  = copy.deepcopy(districts) #You need to append DistrictTemplate
    def to_json(self):
        return copy.deepcopy(vars(self))

class ConstituencyTemplate:
    def __init__(self, updateAt: str='', is_running: bool=False, is_started: bool=False, districts: list=[]):
        self.updateAt   = updateAt
        self.is_running = is_running
        self.is_started = is_started
        self.districts  = copy.deepcopy(districts) #You need to append ConstituencyDistrictTemplate
    def to_json(self):
        return copy.deepcopy(vars(self))

class CountyTemplate:
    def __init__(self, updateAt: str='', is_running: bool=False, is_started: bool=False, districts: list=[]):
        self.updateAt   = updateAt
        self.is_running = is_running
        self.is_started = is_started
        self.districts  = copy.deepcopy(districts) #You need to append DistrictTemplate
    def to_json(self):
        return copy.deepcopy(vars(self))

class TownTemplate:
    def __init__(self, updateAt: str='', is_running: bool=False, is_started: bool=False, districts: list=[]):
        self.updateAt = updateAt
        self.is_running = is_running
        self.is_started = is_started
        self.districts = copy.deepcopy(districts) #You need to append DistrictTemplate, content the data of villages
    def to_json(self):
        return copy.deepcopy(vars(self))

'''
Description:
    Some component templates that you should equip them into skeleton.
'''
class DistrictTemplate:
    def __init__(self, region: str='', county_code: str=None, town: str=None, vill: str=None, type_str: str=None, profRate: float=0.0, candidates: list=[]):
        self.region      = region
        self.county_code = county_code
        self.town       = town
        self.vill       = vill
        self.type       = type_str
        self.profRate   = profRate
        self.candidates = copy.deepcopy(candidates)
        self.note = None   ### specify some different situations about election
    def set_note(self, displayText: str='', displayVotes: bool=False):
        self.note = NoteTemplate(displayText, displayVotes)
    def to_json(self):
        district = {}
        district['range'] = self.region
        district['county'] = self.county_code
        district['town'] = self.town
        district['vill'] = self.vill
        if self.type:
            district['type'] = self.type
        district['profRate'] = self.profRate
        district['candidates'] = self.candidates
        if self.note:
            district['note'] = self.note.to_json()
        return district

class ConstituencyDistrictTemplate:
    def __init__(self, 
                 region: str='', area_nickname: str=None, county_code: str=None, 
                 area: str=None, town: str=None, vill: str=None, type_str: str=None,  
                 profRate: float=0.0, candidates: list=[]
                ):
        self.region        = region
        self.area_nickname = area_nickname
        self.county_code   = county_code
        self.area          = area
        self.town          = town
        self.vill          = vill
        self.type          = type_str
        self.profRate      = profRate
        self.candidates    = copy.deepcopy(candidates)
        self.note = None   ### specify some different situations about election
    def set_note(self, displayText: str='', displayVotes: bool=False):
        self.note = NoteTemplate(displayText, displayVotes)
    def to_json(self):
        district = {
            'range': self.region,
            'area_nickname': self.area_nickname,
            'county': self.county_code,
            'area': self.area,
            'town': self.town,
            'vill': self.vill,
            'type': self.type,
            'profRate': self.profRate,
            'candidates': self.candidates,
        }
        if self.note:
            district['note'] = self.note.to_json()
        return district

class LegislatorDistrictTemplate:
    def __init__(self, region: str='', county_code: str=None, town: str=None, vill: str=None, profRate: float=0.0, candidates: list=[]):
        self.region      = region
        self.county_code = county_code
        self.town       = town
        self.vill       = vill
        self.profRate   = profRate
        self.candidates = copy.deepcopy(candidates)
        self.note = None   ### specify some different situations about election
    def set_note(self, displayText: str='', displayVotes: bool=False):
        self.note = NoteTemplate(displayText, displayVotes)
    def to_json(self):
        district = {
            'range': self.region,
            'county': self.county_code,
            'town': self.town,
            'vill': self.vill,
            'profRate': self.profRate,
            'candidates': self.candidates,
        }
        if self.note:
            district['note'] = self.note.to_json()
        return district

class VillCalcTemplate:
    def __init__(self, region: str='', county: str=None, town: str=None, vill: str=None, voterTurnout: int=0, eligibleVoters: int=0, candidates: list=[]):
        self.region     = region
        self.county     = county
        self.town       = town
        self.vill       = vill
        self.voterTurnout   = voterTurnout
        self.eligibleVoters = eligibleVoters
        self.candidates = copy.deepcopy(candidates)
    def to_json(self):
        return copy.deepcopy(vars(self))

class CandidateTemplate:
    '''
        The candidate template besides party election(不分區立委)
    '''
    def __init__(self, candNo: int=0, name: str='', party: str='', tksRate: float=0.0, candVictor: str=' ', tks: int=0):
        self.candNo = candNo
        self.name = name
        self.party = party
        self.tksRate = tksRate
        self.candVictor = candVictor
        self.tks = tks
    def to_json(self):
        return copy.deepcopy(vars(self))
    
class PartyCandidateTemplate:
    '''
        The candidate template for party election(不分區立委)
    '''
    def __init__(self, candNo: int=0, party: int=0, tksRate: float=0.0, seats: int=0, tks: int=0):
        self.candNo  = candNo
        self.party   = party
        self.tksRate = tksRate
        self.seats   = seats
        self.tks     = tks
    def to_json(self):
        return copy.deepcopy(vars(self))
    
class ErrorTemplate:
    def __init__(self, county=None, town=None, vill=None, reason=None):
        self.county = county
        self.town = town
        self.vill = vill
        self.reason = reason
    def to_json(self):
        return vars(self)