import grequests
import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import pandas as pd
from datetime import datetime
import sys

def progress(count,total):
    sys.stdout.write(f'progress: {count} of {total}\r')
    sys.stdout.flush()

def get_transaction_ids(items):
    transaction_ids = []
    for item in items:
        transaction_ids.append(item['transactionId'])
    return transaction_ids

# boxes.append moved under if condition... test with main function but should work
def get_box_amounts(items,token_id):
    boxes = []
    for box in items:
        for asset in box['assets']:
            if asset['tokenId'] == token_id:
                boxes.append({
                        'boxId' : box['boxId'],
                        'address' : box['address'],
                        'amount' : asset['amount']})
    return boxes

# gets a list of transaction ids for a token id
def get_transaction_list(token_id):
    offset = 0
    r = requests.get(url=f'https://api.ergoplatform.com/api/v1/boxes/byTokenId/{token_id}?limit=1')
    total = r.json()['total']
    s = requests.Session()
    retries = Retry(total=5, backoff_factor=0.2, status_forcelist=[500, 502, 503, 504, 520, 525], raise_on_redirect=True,
                    raise_on_status=True)
    s.mount('http://', HTTPAdapter(max_retries=retries))
    s.mount('https://', HTTPAdapter(max_retries=retries))
    transaction_ids = []
    responses = []
    while offset <= total:
        progress(offset,total)
        urls = []
        while offset <= total and len(urls) < 20:
            urls.append(f'https://api.ergoplatform.com/api/v1/boxes/byTokenId/{token_id}?limit=100&offset={offset}')
            offset += 100
        rs = (grequests.get(u, session=s) for u in urls)
        rl = grequests.map(rs)
        responses = responses + rl
    for r in responses:
        if r.status_code != 200:
            print(r.status_code)
        data = r.json()
        transaction_ids = transaction_ids + get_transaction_ids(data['items'])
    progress(total,total)
    return transaction_ids

def parse_transaction(data,token_id):
    outputs = get_box_amounts(data['outputs'],token_id)
    inputs = get_box_amounts(data['inputs'],token_id)
    for input in inputs:
        input['amount'] = input['amount'] * -1
    

def get_transaction_details(transaction_ids,token_id):
    total = len(transaction_ids)
    s = requests.Session()
    retries = Retry(total=5, backoff_factor=0.2, status_forcelist=[500, 502, 503, 504, 520, 525], raise_on_redirect=True,
                    raise_on_status=True)
    s.mount('http://', HTTPAdapter(max_retries=retries))
    s.mount('https://', HTTPAdapter(max_retries=retries))
    transaction_ids = []
    responses = []
    urls = []
    for transaction_id in transaction_ids:
        urls.append(f'https://api.ergoplatform.com/api/v1/transactions/{transaction_id}')

    for i in range(0,total,20):
        rs = (grequests.get(u, session=s) for u in urls[i:i+20])
        rl = grequests.map(rs)
        responses = responses + rl
    for r in responses:
        if r.status_code != 200:
            print(r.status_code)
        data = r.json()
        
    progress(total,total)
    return transaction_ids