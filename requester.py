import time

import requests

waits = [10, 30, 120, 300]
current_wait = 0


def get(url: str, **kwargs):
    global current_wait
    while True:
        try:
            res = requests.get(url, **kwargs)
            current_wait = 0
            return res
        except requests.ConnectionError:
            print('Connection error. Next retry in %d seconds' % waits[current_wait])
            time.sleep(waits[current_wait])
            current_wait += 1 if current_wait < len(waits)-1 else 0


def post(url: str, **kwargs):
    global current_wait
    while True:
        try:
            res = requests.post(url, **kwargs)
            current_wait = 0
            return res
        except requests.ConnectionError:
            print('Connection error. Next retry in %d seconds' % waits[current_wait])
            time.sleep(waits[current_wait])
            current_wait += 1 if current_wait < len(waits)-1 else 0
