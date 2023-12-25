from gql.transport.aiohttp import AIOHTTPTransport
from gql import gql, Client
import asyncio

'''
  GQL function
'''
async def gql2json(gql_endpoint, gql_string):
    gql_transport = AIOHTTPTransport(url=gql_endpoint)
    gql_client = Client(transport=gql_transport,
                        fetch_schema_from_transport=False)

    query = gql(gql_string)
    json_data = await gql_client.execute_async(query)
    return json_data


'''
  Queries string for each election type
'''

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

gql_plainIndigeous_2024 = """
query GetPlainIndigeous {
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