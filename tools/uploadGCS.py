from google.cloud import storage
from datetime import datetime
from configs import upload_configs
import os
import json

IS_TV =  os.environ['PROJECT'] == 'tv' 
BUCKET = os.environ['BUCKET']
ENV_FOLDER = os.environ['ENV_FOLDER']
VERSION = os.environ['VERSION']

def upload_folder_async(resource_folder):
    '''
        Upload a specific folder asynchronously
    '''
    os.system('gcloud auth activate-service-account --key-file=gcs-key.json')
    max_age = upload_configs['cache_control_short']
    os.system(f'gsutil -q -m -h "Cache-Control: {max_age}" rsync -r {resource_folder} gs://{BUCKET}/{resource_folder} &')

def upload_multiple(year, upload_map: bool=False, upload_v2: bool=False):
    '''
        You can call this function to upload folder onto bucket
    '''
    os.system('gcloud auth activate-service-account --key-file=gcs-key.json')
    max_age = upload_configs['cache_control_short']
    if upload_map:
        print('gsutil upload map')
        os.system(f'gsutil -q -m -h "Cache-Control: {max_age}" rsync -r {ENV_FOLDER}/{year} gs://{BUCKET}/{ENV_FOLDER}/{year} &')
    if upload_v2:
        print('gsutil upload v2')
        os.system(f'gsutil -q -m -h "Cache-Control: {max_age}" rsync -r {ENV_FOLDER}/{VERSION}/{year} gs://{BUCKET}/{ENV_FOLDER}/{VERSION}/{year} &')# vote comparing

def upload_multiple_folders(year):
    '''
        You can call this function to upload folder onto bucket, with cache-control
    '''
    os.system('gcloud auth activate-service-account --key-file=gcs-key.json')
    max_age = upload_configs['cache_control_short'] if year == datetime.now().year else upload_configs['cache_control']
    if IS_TV:
        os.system(f'gsutil -m -h "Cache-Control: {max_age},must-revalidate" rsync -r {ENV_FOLDER} gs://{BUCKET}/{ENV_FOLDER}')
    else:
        os.system(f'gsutil -m -h "Cache-Control: {max_age}" rsync -r {ENV_FOLDER}/{year} gs://{BUCKET}/{ENV_FOLDER}/{year} &')#map infobox seat
        os.system(f'gsutil -m -h "Cache-Control: {max_age}" rsync -r {ENV_FOLDER}/{VERSION}/{year} gs://{BUCKET}/{ENV_FOLDER}/{VERSION}/{year} &')# vote comparing

def upload_blob_realtime(dest_filename):
    storage_client = storage.Client().from_service_account_json('gcs-key.json')
    bucket = storage_client.bucket(os.environ['BUCKET'])
    blob = bucket.blob(dest_filename)
    blob.upload_from_filename(dest_filename)
    blob.cache_control = upload_configs['cache_control_long']
    blob.patch()

def upload_blob(dest_filename, year):
    '''
    Description:
        Upload the destination file onto GCS bucket.

    How to use:
        You should call save_file() first to store your data as file, and then call upload_blob()
        to upload to GCS.
        No need to worry about whether the directory exists. As you specify the dest_filename, GCS
        will create the directory automatically for you.
    
    Note:

    '''
    storage_client = storage.Client().from_service_account_json('gcs-key.json')
    bucket = storage_client.bucket(os.environ['BUCKET'])
    blob = bucket.blob(dest_filename)
    blob.upload_from_filename(dest_filename)
    #print("File {} uploaded to {}.".format(dest_filename, dest_filename))
    if year == datetime.now().year:
        blob.cache_control = upload_configs['cache_control_short']
    else:
        blob.cache_control = upload_configs['cache_control']
    blob.patch()


def save_file(dest_filename, data, year=None):
    '''
    Description:
        Store the data into dest_filename. Currently, we only support json type storage.
    
    How to use:
        If you want to store the data in 'election-dev/2024/county/09007.json'
        Call this function with dest_filename='election-dev/2024/county/09007.json', and give the data.
        This function will create directory automatically for you, don't need to worry about it.
    
    Note:
        input parameter 'year' will be deprecated in the future.
    '''
    if data:
        dirname = os.path.dirname(dest_filename)
        if len(dirname)>0 and not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(dest_filename, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False))

def open_file(filename, encoding='utf-8'):
    '''
     The type of encoding depends on os environment,
     For example, default encoding of Windows is cp1252 or utf-8, and Linux is utf-8.
    '''
    data = {}
    if os.path.isfile(filename):
        with open(filename, encoding=encoding) as f:
            data = json.load(f)
    return data