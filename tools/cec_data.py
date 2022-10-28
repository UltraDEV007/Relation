import requests
import os
import json

def request_cec():
    r = requests.get(os.environ['CECURL'],auth=(os.environ['USERNAME'], os.environ['PASSWD']))
    if r.status_code == 200:
        new_data = json.loads(r.text)
        if os.path.isfile('running.json'):
            with open('running.json') as f:
                running = json.loads(f.read())
            if running['ST'] == new_data['ST']:
                print('the same cec data.')
                return False
        with open('running.json', 'w') as f:
            f.write(r.text)
        return new_data
    else:
        print('cant get cec data.')
        return False

if __name__=='__main__':
    data = request_cec()
    print("done")
