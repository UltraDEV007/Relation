import requests
import os
import json

def request_cec():
    r = requests.get(os.environ['CECURL'],auth=(os.environ['USERNAME'], os.environ['PASSWD']))
    if r.status_code == 200:
        return json.loads(r.text)
    else:
        print('cant get cec data.')
        return False

if __name__=='__main__':
    request_cec()
