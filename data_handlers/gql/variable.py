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
