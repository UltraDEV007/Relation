'''
    When we send mutation request to GQL, we need to provide the variable which contents
    the modification data.
'''
import copy

class PersonVariable:
    def __init__(self, votes_obtained_number: str, votes_obtained_percentage: str, elected: bool, id: str):
        self.id = id
        self.data = {}
        self.data['votes_obtained_number']     = votes_obtained_number
        self.data['votes_obtained_percentage'] = votes_obtained_percentage
        self.data['elected']                   = elected
    def to_json(self):
        return copy.deepcopy(vars(self))
    
class PartyVariable:
    def __init__(self, votes_obtained_number: str, first_obtained_number: str, second_obtained_number: str, seats: str, id: str):
        self.id = id
        self.data = {}
        self.data['votes_obtained_number']   = votes_obtained_number
        self.data['first_obtained_number']   = first_obtained_number
        self.data['second_obtained_number']  = second_obtained_number
        self.data['seats']                   = seats
    def to_json(self):
        return copy.deepcopy(vars(self))
