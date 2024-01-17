'''
Provide function to fetch data from WHORU and modify data
'''
from gql.transport.aiohttp import AIOHTTPTransport
from gql import gql, Client

def gql_fetch(gql_endpoint, gql_string):
    gql_transport = AIOHTTPTransport(url=gql_endpoint)
    gql_client = Client(transport=gql_transport,
                        fetch_schema_from_transport=True)

    json_data = gql_client.execute(gql(gql_string))
    return json_data
    
def gql_update(gql_endpoint, gql_string, gql_variable):
    gql_transport = AIOHTTPTransport(url=gql_endpoint)
    gql_client = Client(transport=gql_transport,
                        fetch_schema_from_transport=True)
    json_data = gql_client.execute_async(gql(gql_string), variable_values=gql_variable)
    return json_data
