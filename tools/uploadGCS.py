from google.cloud import storage
from datetime import datetime
from configs import upload_configs


def upload_blob(destination_file, year):

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
