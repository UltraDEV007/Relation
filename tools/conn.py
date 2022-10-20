from gql.transport.aiohttp import AIOHTTPTransport
from gql import Client
from configs import gql_url


def gql_client():
    transport = AIOHTTPTransport(url=gql_url)
    return Client(transport=transport, fetch_schema_from_transport=True)