'''
    When we send mutation request to GQL, we need to provide the variable which contents
    the modification data.
'''
import copy

class UpdatePersonElectionVariable:
    def __init__(self, votes_obtained_number: str, votes_obtained_percentage: str, elected: bool, id: str):
        self.id = id
        self.data = {}
        self.data['votes_obtained_number']     = votes_obtained_number
        self.data['votes_obtained_percentage'] = votes_obtained_percentage
        self.data['elected']                   = elected
    def to_json(self):
        return copy.deepcopy(vars(self))
    
class UpdatePartyElectionVariable:
    def __init__(self, votes_obtained_number: str, first_obtained_number: str, second_obtained_number: str, seats: str, id: str):
        self.id = id
        self.data = {}
        self.data['votes_obtained_number']   = votes_obtained_number
        self.data['first_obtained_number']   = first_obtained_number
        self.data['second_obtained_number']  = second_obtained_number
        self.data['seats']                   = seats
    def to_json(self):
        return copy.deepcopy(vars(self))


'''
    TermOffice: Used to mark the term of office(任期)
'''
class TermOffice:
    def __init__(self, start_date_year: int, start_date_month: int, start_date_day: int, end_date_year: int, end_date_month: int, end_date_day: int):
        self.start_date_year  = start_date_year
        self.start_date_month = start_date_month
        self.start_date_day   = start_date_day
        self.end_date_year    = end_date_year
        self.end_date_month   = end_date_month
        self.end_date_day     = end_date_day
    def to_json(self):
        return copy.deepcopy(vars(self))
termOffice_president_2024 = TermOffice(
    start_date_year  = 2024,
    start_date_month = 5,
    start_date_day   = 20,
    end_date_year    = 2028,
    end_date_month   = 5,
    end_date_day     = 20
).to_json()
termOffice_legislator_2024 = TermOffice(
    start_date_year  = 2024,
    start_date_month = 2,
    start_date_day   = 1,
    end_date_year    = 2028,
    end_date_month   = 1,
    end_date_day     = 31
).to_json()

'''
    CreatePersonOrganizationVariable: Create person organization, term_office must to be TermOffice(...).to_json()
'''
class CreatePersonOrganizationVariable:
    def __init__(self, person_id: str, organization_id: str, election_id: str, role: str, source: str, term_office: dict):
        self.data = {}
        self.data['person_id'] = {
            "connect": {
                "id": person_id
            }
        }
        self.data['organization_id'] = {
            "connect": {
                "id": organization_id
            }
        }
        self.data['election'] = {
            "connect": {
                "id": election_id
            }
        }
        self.data['role'] = role
        self.data['source'] = source
        self.data['start_date_year']  = term_office['start_date_year']
        self.data['start_date_month'] = term_office['start_date_month']
        self.data['start_date_day']   = term_office['start_date_day']
        self.data['end_date_year']    = term_office['end_date_year']
        self.data['end_date_month']   = term_office['end_date_month']
        self.data['end_date_day']     = term_office['end_date_day']
    def to_json(self):
        return copy.deepcopy(vars(self))
