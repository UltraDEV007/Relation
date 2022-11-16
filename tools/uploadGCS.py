from google.cloud import storage
from datetime import datetime
from configs import upload_configs
import os
import json


def upload_blob(destination_file, year, project):
    if project == 'tv':
        storage_client = storage.Client()
        bucket = storage_client.bucket(os.environ['TV_BUCKET'])
    else:
        storage_client = storage.Client().from_service_account_json('readr-key.json')
        bucket = storage_client.bucket(upload_configs['bucket_name'])
    blob = bucket.blob(destination_file)
    blob.upload_from_filename(destination_file)
    print("File {} uploaded to {}.".format(destination_file, destination_file))
    if year == datetime.now().year:
        blob.cache_control = upload_configs['cache_control_short']
    else:
        blob.cache_control = upload_configs['cache_control']
    blob.content_type = upload_configs['content_type_json']
    blob.patch()
    print("The metadata configuration for the blob is complete")


def save_file(destination_file, data, year, project='readr'):
    if project == 'tv':
        destination_file = 'json/' + destination_file.replace('-dev', '')
    if not os.path.exists(os.path.dirname(destination_file)):
        os.makedirs(os.path.dirname(destination_file))
    with open(destination_file, 'w') as f:
        f.write(json.dumps(data, ensure_ascii=False))
    upload_blob(destination_file, year, project)
