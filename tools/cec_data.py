import requests
import os
import json

CECURL_RF = os.environ.get('CECURL_RF')
CECURL_GENERAL = os.environ.get('CECURL_GENERAL')

def check_cec_2024():
    filename = "running.json"
    url = f"{CECURL_RF}{filename}"
    
    ### We disable SSL certificate authentication here...but it might need...
    r = requests.get(url=url, auth=(os.environ['USERNAME'], os.environ['PASSWD']), verify=False)
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        print(f"Couldn't get CEC data from {url}")
        return
    new_data = json.loads(r.text)
    return new_data

def check_updated_and_save(url):
    filename = url.split('/')[-1]
    r = requests.get(url=url, auth=(os.environ['USERNAME'], os.environ['PASSWD']))
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
        json.dump(new_data, f)
    return new_data


def request_cec(filename):
    url = f"{os.environ['CECURL']}{filename}"
    return check_updated_and_save(url)


def request_cec_by_type(type: str = 'general'):
    cec_url = CECURL_RF if type == 'rf' else CECURL_GENERAL
    fin_url = f"{cec_url}final.json"
    run_url = f"{cec_url}running.json"
    
    fin_data = check_updated_and_save(fin_url)
    if fin_data:
        return fin_data, False

    run_data = check_updated_and_save(run_url)
    if run_data:
        return run_data, True

    print("Couldn't get CEC data from either final or running URL.")
    return None, None


if __name__ == '__main__':
    data = request_cec('running.json')
    data = request_cec('final.json')
    # data = request_cec()
    print("done")
