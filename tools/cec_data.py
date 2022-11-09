import requests
import os
import json

def check_url(url):
    r = requests.get(url = url,auth=(os.environ['USERNAME'], os.environ['PASSWD']))
    filename = url.split('/')[-1]
    if r.status_code == 200:
        new_data = json.loads(r.text)
        if os.path.isfile(filename):
            with open(filename) as f:
                running = json.loads(f.read())
            if running['ST'] == new_data['ST']:
                print('the same cec data.')
                return False
        with open(filename, 'w') as f:
            f.write(r.text)
        return new_data
    print(f'cant get cec {filename} data.')
    return False


def request_cec(filename):
    url = f"{os.environ['CECURL']}{filename}"
    return check_url(url)

def request_cec_by_type(type='general'):
    RUNNING = 'running.json'
    FINAL = 'final.json'
    if type == 'general':
        fin_url = f"{os.environ['CECURL_GENERAL']}{FINAL}"
        run_url = f"{os.environ['CECURL_GENERAL']}{RUNNING}"
    elif type == 'rf':
        fin_url = f"{os.environ['CECURL_RF']}RF{FINAL}"
        run_url = f"{os.environ['CECURL_RF']}RF{RUNNING}"
    fin_data = check_url(fin_url)
    if fin_data:
        return fin_data
    else:
        run_data = check_url(run_url)
        if run_data:
            return run_data
    return False

if __name__=='__main__':
    data = request_cec('running.json')
    # data = request_cec('final.json')
    data = request_cec()
    print("done")
