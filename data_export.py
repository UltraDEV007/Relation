import os
import json
import requests
import pygsheets
from gql.transport.aiohttp import AIOHTTPTransport
from gql import gql, Client
from google.cloud import storage

def president2024_realtime():
    gc = pygsheets.authorize(service_account_env_var = 'GDRIVE_API_CREDENTIALS')
    url = "https://docs.google.com/spreadsheets/d/1Ar9r7j5LN6eCirNnQ5Lkbl4IEw3UaDQMfdBq5b2oDOE/edit#gid=1764492368"
    sht = gc.open_by_url( url )
    voting_data = { "result": [] }
    try:
        meta_sheet = sht.worksheet_by_title("官網切換相關")
    except Exception as e:
        print("Exception: {}".format(type(e).__name__))
        print("Exception message: {}".format(e))

    voting_data['title'] = meta_sheet.get_value("B2")
    get_cec_data = meta_sheet.get_value("B3")
    switch_view = meta_sheet.get_value("B4")
    cec_data = {}
    readr_data = {}
#    if switch_view == 'T' or get_cec_data == 'T':
    cec_json= requests.get('https://whoareyou-gcs.readr.tw/elections-dev/2024/president/map/country/country.json')
    if cec_json.status_code == 200:
        cec_data = json.loads(cec_json.text)
        readr_data["updateAt"] = cec_json["updateAt"]
        voting_data["updateAt"] = cec_json["updateAt"]
        # upload for pure cec data
        readr_data["title"] = "2024 總統大選即時開票"
        readr_data["result"] = presindent2024_cec( cec_data["summary"], 2 )
        upload_data('whoareyou-gcs.readr.tw', json.dumps(readr_data, ensure_ascii=False).encode('utf8'), 'application/json', "json/2024cec_homepage.json")

    if switch_view == 'T':
        print("Getting the final data")
        voting_data["result"] = presindent2024_cec( cec_data["summary"], 2 )
    else:
        try:
            result_sheet = sht.worksheet_by_title("官網票數")
        except Exception as e:
            print("Exception: {}".format(type(e).__name__))
            print("Exception message: {}".format(e))

        candidates = result_sheet.get_values("B1", "D1")
        sheet_tks = result_sheet.get_values("A2", "D6")
        for row in sheet_tks:
            unit_tks = { "key": row[0], "value": [] }
            for number in range(len(candidates[0])):
                unit_tks['value'].append( { candidates[0][number][0:1]: row[number + 1].replace(",", "") })
                #unit_tks[candidates[0][number]] = row[number]
            voting_data["result"].append(unit_tks)
                
        print("Getting data from sheet")
        if get_cec_data == 'T':
            for result in voting_data["result"]:
                if "key" in result and result["key"] == '鏡新聞':
                    result["value"] = presindent2024_cec( cec_data["summary"] )
            print("Replace the mnews data by cec data")

    upload_data('whoareyou-gcs.readr.tw', json.dumps(voting_data, ensure_ascii=False).encode('utf8'), 'application/json', "json/2024homepage.json")
    return "OK"

def presindent2024_cec( summary, phase = 1 ):
    tks = []
    tksRate = []
    candVictor = []
    show_victor = False
    for candidate in summary["candidates"]:
        if candidate["candNo"] < 4:
            tks.append({candidate["candNo"]: candidate["tks"]})
            tksRate.append({candidate["candNo"]: candidate["tksRate"]})
            candVictor.append({candidate["candNo"]: candidate["candVictor"]})
            if candidate["candVictor"]:
                show_victor = True
    if phase == 1:
        final = tks
    else:
        cec_candidates = []
        if show_victor:
            cec_candidates.append({"key": "當選", "value": candVictor})
        cec_candidates.append({"key": "得票數", "value": tks})
        cec_candidates.append({"key": "得票率", "value": tksRate})
        final = cec_candidates
    return final

def sheet2json( url, sheet ):
    gc = pygsheets.authorize(service_account_env_var = 'GDRIVE_API_CREDENTIALS')
    sht = gc.open_by_url( url )

    sheet_titles = sheet.split(',')
    sheets_obj = {}
    for sheet_title in sheet_titles:
        try:
            meta_sheet = sht.worksheet_by_title(sheet_title)
        except Exception as e:
            print("Exception: {}".format(type(e).__name__))
            print("Exception message: {}".format(e))
            continue

        meta_data = meta_sheet.get_all_values()
        #if sheet_name == 'translateurl_for_website':
        #    field_shift = 1
        #else:
        #    field_shift = 0

        field_names = [field_name for field_name in meta_data[0] if field_name != '']
        all_rows = []
        sheet_title_lower = sheet_title.lower()
        if sheet_title_lower in {'pageinfo', 'partners'}:
            all_rows = {}
        
        for i in range(1, len(meta_data)):
            row = meta_data[i]
            if not row[0]:
                break

            values = {field_name:value for field_name, value in zip(field_names[1:], row[1:])}
            if sheet_title_lower == 'pageinfo':
                all_rows[row[0]] = values
            elif sheet_title_lower == 'partners':
                if row[0] in all_rows:
                    all_rows[row[0]].append(values)
                else:
                    all_rows[row[0]] = [values]
            else:
                values = {field_name:value for field_name, value in zip(field_names, row)}
                all_rows.append(values)

        sheets_obj[sheet_title] = all_rows
    return sheets_obj
	

def gql2json(gql_endpoint, gql_string):
    #bucket = os.environ['BUCKET']
    #destination = os.environ('DEST']
    gql_transport = AIOHTTPTransport(url=gql_endpoint)
    gql_client = Client(transport=gql_transport,
                        fetch_schema_from_transport=False)
    # sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

    query = gql(gql_string)
    json_data = gql_client.execute(query)
    #upload_data(bucket, json.dumps(json_data, ensure_ascii=False).encode('utf8'), 'application/json', gcs_path + DEST)
    return json_data

def upload_data(bucket_name: str, data: str, content_type: str, destination_blob_name: str):
    '''Uploads a file to the bucket.'''
    # bucket_name = 'your-bucket-name'
    # data = 'storage-object-content'
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    # blob.content_encoding = 'gzip'
    # try:
    #       data=bytes(data, encoding='utf-8'),
    # except:
    #     print(data)
    blob.upload_from_string(
        # data=gzip.compress(data=data, compresslevel=9),
        #data=bytes(data, encoding='utf-8'),
        data,
        content_type=content_type, client=storage_client)
    blob.content_language = 'zh'
    blob.cache_control = 'max-age=300,public'
    blob.patch()

if __name__ == "__main__":  
    gql_string = """
query { allPosts(where: { tags_every: {name_in: "疫苗"}, state: published }, orderBy: "publishTime_DESC", first: 3) {
    style
    title: name
	slug
    brief
    briefApiData
    contentApiData
    publishTime
    heroImage {
      tiny: urlTinySized
      mobile: urlMobileSized
      tablet: urlTabletSized
      desktop: urlDesktopSized
    } 
    updatedAt
    source
    isAdult
  }
}
"""
    #gql_endpoint = "https://api-dev.example.com"
    #gql2json(gql_endpoint, gql_string)
    keyfile = {
    }
    os.environ['GDRIVE_API_CREDENTIALS'] = json.dumps(keyfile)
    #sheet_content = president2024_realtime("https://docs.google.com/spreadsheets/d/1Ar9r7j5LN6eCirNnQ5Lkbl4IEw3UaDQMfdBq5b2oDOE/edit#gid=1764492368")
    sheet_content = president2024_realtime()
    print(sheet_content)
