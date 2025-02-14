import requests
import os
import json
from tools.uploadGCS import save_file

CECURL_RF = os.environ.get('CECURL_RF')
CECURL_GENERAL = os.environ.get('CECURL_GENERAL')
SAVE_CEC = os.environ.get('SAVE_CEC', 'false') == 'true'

cec_filename = ['final.json', 'running.json']
cec_legislator = ['final_A.json'] # TODO: How to deal with it?

def check_existed_cec_file():
    raw_data = None
    is_running = False

    ### check final.json
    if os.path.isfile(cec_filename[0]):
        with open(cec_filename[0]) as f:
            raw_data = json.load(f)
    else:
        if os.path.isfile(cec_filename[1]):
            with open(cec_filename[1]) as f:
                raw_data = json.load(f)
                is_running = True
    return raw_data, is_running
            

def check_updated_and_save(url, secure_mode=False):
    filename = url.split('/')[-1]
    
    # TODO: SSL verify mode, we should guarantee SSL mode and None-SSL mode
    r = requests.get(url=url, auth=(os.environ['USERNAME'], os.environ['PASSWD']), verify=secure_mode)
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        print(f"Couldn't get CEC data from {url}")
        return
    
    new_data = json.loads(r.text)
    if os.path.isfile(filename):
        with open(filename) as f:
            old_data = json.load(f)
        if old_data['ST'] == new_data['ST']: # update time
            print('The same CEC data.')
            return
    with open(filename, 'w') as f:
        print(f'Update data for {filename}')
        json.dump(new_data, f)
    ### Save the file for future usage
    if SAVE_CEC:
        start_time = new_data['ST']
        folder = os.path.join(os.environ['ENV_FOLDER'], 'cec-data')
        save_file(os.path.join(folder, f'{start_time}{filename}'), new_data)
    return new_data

def request_cec(filename, secure_mode=False):
    '''
        Description:
            Single operation to check the updating state for filename.
        Input:
            filename        - "final.json", "final_A.json", "running.json"
        Output:
            received_data   - The received json data
    '''
    url = f"{os.environ['CECURL']}{filename}"
    return check_updated_and_save(url, secure_mode)

def request_cec_by_type(type: str = 'general', secure_mode=False):
    '''
        Description:
            Batch operation to check the updating state for each json in cec_dataname,
            need to be careful that the sequence in cec_datatype does matter.
        Input:
            type            - It's same currently
        Output:
            received_data   - The received json data
            is_running      - False: final, True: running
    '''
    cec_url = CECURL_RF if type == 'rf' else CECURL_GENERAL
    is_running = False

    for idx, filename in enumerate(cec_filename):
        is_running = True if idx==(len(cec_filename))-1 else False
        data_url = f"{cec_url}{filename}"
        received_data = check_updated_and_save(data_url, secure_mode)
        if received_data:
            return received_data, is_running

    print("Couldn't get CEC data from either final or running URL.")
    return None, None

def request_url(url):
    '''
        Get the cec data from url, used to fetch data from bucket
    '''
    cec_data = None
    cec_json= requests.get(url)
    if cec_json.status_code == 200:
        cec_data = json.loads(cec_json.text)
    return cec_data

if __name__ == '__main__':
    for filename in cec_filename:
        receive_data = request_cec(filename)

    print("done")
