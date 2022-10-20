from gql.transport.aiohttp import AIOHTTPTransport
from gql import Client
import os


def gql_client():
    transport = AIOHTTPTransport(url=os.environ.get('GQL_URL'))
    return Client(transport=transport, fetch_schema_from_transport=True)