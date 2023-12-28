'''
Description:
    Transformer is used to transform data from ris.gov.tw(戶役政資訊系統).
    
Data Resources:
    戶役政資訊系統資料代碼內容清單: https://www.ris.gov.tw/documents/html/5/1/168.html
    Please download each of the following files on your local machine.
    1. 省市縣市代碼(mapping_prv_city)
    2. 縣市代碼(mapping_city)
    3. 省市縣市鄉鎮代碼(mapping_prv_city_vill)

How to use:    
    You should copy the code in your local environment and generate each of the files listed above.
    The result are json format files, and you can paste them in this project/mapping folder.
'''

def transform_mapping(filepath):
    mapping = {}
    with open(filepath, mode='r') as f:
        for line in f:
            key, value = line.strip().split('=')
            key = int(key)
            mapping[key] = value
    return mapping