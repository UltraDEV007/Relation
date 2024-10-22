'''
  Queries string for each election type
'''
def get_president_string(year):
    gql_string = gql_president_2024
    if year=='2024':
        gql_string = gql_president_2024
    return gql_string

def get_mountain_indigeous_string(year):
    gql_string = gql_mountainIndigeous_2024
    if year=='2024':
        gql_string = gql_mountainIndigeous_2024
    return gql_string

def get_plain_indigeous_string(year):
    gql_string = gql_plainIndigeous_2024
    if year=='2024':
        gql_string = gql_plainIndigeous_2024
    return gql_string

def get_party_oe_string(year):
    gql_string = gql_party_oe_2024
    if year=='2024':
        gql_string = gql_party_oe_2024
    return gql_string

def get_party_pe_string(year):
    gql_string = gql_party_pe_2024
    if year=='2024':
        gql_string = gql_party_pe_2024
    return gql_string

def get_normal_string(year):
    gql_string = gql_constituency_2024
    if year=='2024':
        gql_string = gql_constituency_2024
    return gql_string

gql_president_2024 = """
query GetPresidents {
  personElections(
    orderBy:{ number: asc },
    where: {
      election: {id: { equals: 85 } },
      status: {equals: "active"},
    }) {
    id
    number
    mainCandidate {
      person_id {
        id
        name
      }
    }
    party {
      id
      name
    }
    person_id {
      id
      name
      image
    }
  }
}
"""

gql_mountainIndigeous_2024 = """
query GetMountainIndigeous {
  personElections(
    orderBy:{ number: asc },
    where: {
      election: {id: { equals: 88 } },
      status: {equals: "active"},
    }) {
    id
    number
    party {
      id
      name
    }
    person_id {
      id
      name
      image
    }
  }
}
"""

gql_plainIndigeous_2024 = """
query GetPlainIndigeous {
  personElections(
    orderBy:{ number: asc },
    where: {
      election: {id: { equals: 89 } },
      status: {equals: "active"},
    }) {
    id
    number
    party {
      id
      name
    }
    person_id {
      id
      name
      image
    }
  }
}
"""

### Organization election query for legislator party
gql_party_oe_2024 = """
query GetParty {
  organizationsElections(
    orderBy:{ number: asc },
    where: {
      elections: {id: { equals: 86 } },
    }) {
    id
    number
    organization_id {
      id
      name
    }
  }
}
"""

### Person election query for legislator party
gql_party_pe_2024 = """
query GetParty {
  personElections(
    orderBy:{ number: asc },
    where: {
      election: {id: { equals: 86 } },
      status: {equals: "active"},
    }) {
    id
    party {
      id
      name
    }
    person_id {
      id
      name
    }
    legislatoratlarge_number
  }
}
"""

gql_constituency_2024 = """
query GetConstituency {
  personElections(
    orderBy:{ number: asc },
    where: {
      election: {id: { equals: 87 } },
      status: {equals: "active"},
    }) {
    id
    number
    electoral_district{
      city
      name
    }
    party {
      name
    }
    person_id {
      id
      name
      image
    }
  }
}
"""

gql_organizations_string = """
query GetOrganizations {
  organizations(orderBy:{ id: asc }) {
    id
    name
  }
}
"""

'''
  Update queries
'''
gql_update_person = """
mutation ($data: PersonElectionUpdateInput!, $id: ID!) {
  item: updatePersonElection(where: {id: $id}, data: $data) {
    id
    person_id {
      name
    }
    votes_obtained_number
    votes_obtained_percentage
    elected
  }
}
"""

gql_update_party = """
mutation($data: OrganizationsElectionUpdateInput!, $id: ID!) {
  item: updateOrganizationsElection(where: {id: $id}, data: $data) {
    id
    votes_obtained_number
    first_obtained_number
    second_obtained_number
    seats
  }
}

"""

'''
  Create queries
'''
gql_create_personOrganization = """
mutation ($data: PersonOrganizationCreateInput!) {
  item: createPersonOrganization(data: $data) {
    id
  }
}
"""