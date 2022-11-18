from google.cloud import storage
from datetime import datetime
from configs import upload_configs
import os
import json

IS_TV =  os.environ['PROJECT'] == 'tv' 
BUCKET = os.environ['BUCKET']
ENV_FOLDER = os.environ['ENV_FOLDER']


def upload_multiple_folders():
    os.system('gcloud auth activate-service-account --key-file=gcs-key.json')
    if IS_TV:
        os.system(f'gsutil -m -h "Cache-Control: max-age=30" rsync -r {ENV_FOLDER} gs://{BUCKET}/{ENV_FOLDER}')
    else:
        os.system(f'gsutil -m -h "Cache-Control: max-age=30" rsync -r {ENV_FOLDER}/2022 gs://{BUCKET}/{ENV_FOLDER}/2022')
        os.system(f'gsutil -m -h "Cache-Control: max-age=30" rsync -r {ENV_FOLDER}/v2/2022 gs://{BUCKET}/{ENV_FOLDER}/v2/2022')
    
def upload_blob(destination_file, year):
    storage_client = storage.Client().from_service_account_json('gcs-key.json')
    bucket = storage_client.bucket(os.environ['BUCKET'])
    blob = bucket.blob(destination_file)
    blob.upload_from_filename(destination_file)
    print("File {} uploaded to {}.".format(destination_file, destination_file))
    if year == datetime.now().year:
        blob.cache_control = upload_configs['cache_control_short']
    else:
        blob.cache_control = upload_configs['cache_control']
    blob.patch()


def save_file(destination_file, data, year):
    if not os.path.exists(os.path.dirname(destination_file)):
        os.makedirs(os.path.dirname(destination_file))
    with open(destination_file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False))
    # print(destination_file)
