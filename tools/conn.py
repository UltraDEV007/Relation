from gql.transport.aiohttp import AIOHTTPTransport
from gql import Client
import os
import pygsheets



def get_sht_data(url, shtID):
    gc = pygsheets.authorize(service_file='sht-key.json')
    sht = gc.open_by_url(url) 
    wks = sht.worksheet('id', shtID)
    # wks = sht.worksheet_by_title(title)
    return wks.get_all_values()

def gql_client():
    transport = AIOHTTPTransport(url=os.environ.get('GQL_URL'))
    return Client(transport=transport, fetch_schema_from_transport=True)
