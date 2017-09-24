#! /usr/bin/env python3
import getopt
import datetime as dt
import re
import os

import time

import sys
from bs4 import BeautifulSoup

from parser2 import handle_data
import requester as requests

timeout = 2

location = None
start_date = None
end_date = None

BASE_URL = 'https://www.tripadvisor.com/'
DATE_FORMAT = "%m/%d/%Y"

searchSessionId = None


def make_request_options():
    return {}


def parse_response(text):
    return []


def write_row(item):
    pass


def get_site_page_name(query):
    data = {
        'action': 'API',
        'types': 'geo, air, nbrhd, hotel, theme_park',
        'filter': '',
        'legacy_format': 'true',
        'urlList': 'true',
        'strictParent': 'true',
        'query': query,
        'max': 6,
        'name_depth': 3,
        'interleaved': 'true',
        'scoreThreshold': 0.5,
        'strictAnd': 'false',
        'typeahead1_5': 'true',
        'disableMaxGroupSize': 'true',
        'geoBoostFix': 'true',
        'neighborhood_geos': 'true',
        'details': 'true',
        'link_type': 'hotel,vr,eat,attr',
        'uiOrigin': 'trip_search_Hotels',
        'source': 'trip_search_Hotels',
        'startTime': int(time.time()),
        'searchSessionId': searchSessionId
    }

    r = requests.get(BASE_URL + 'TypeAheadJson', params=data)

    resp = r.json()
    return resp[0]['url']


def get_cookie(begin: dt.datetime, end: dt.datetime):
    stay_dates = begin.strftime('%Y_%m_%d_') + end.strftime('%Y_%m_%d')
    form_data = {
        "staydates": stay_dates,
        "adults": 1,
        "rooms": 1,
        "child_rm_ages": ''
    }
    r = requests.post('https://www.tripadvisor.ru/UpdateSessionDatesAjax', data=form_data)
    return r.cookies


def get_other_pages(page: str):
    soup = BeautifulSoup(page, 'html.parser')
    res = []
    try:
        last_page_number = soup.find_all('a', {'class': 'last'})[0]['data-page-number']
    except IndexError:
        return []

    for i in range(1, int(last_page_number)):
        href = soup.find_all('a', {'class': 'pageNum'})[0]['href']
        offset = i * 30
        a = re.split(r'oa[0-9]{0,5}', href)
        if i > 0:
            next_link = ''.join([a[0], 'oa', str(offset), a[1]])
        else:
            next_link = ''.join([a[0][:len(a[0]) - 1], a[1]])
        res.append(next_link)
    return res


def init_ssid():
    r = requests.get(BASE_URL)
    soup = BeautifulSoup(r.text, 'html.parser')
    global searchSessionId
    searchSessionId = soup.find('input', {'name': 'searchSessionId'})['value']


def main(location, start_date, end_date):
    init_ssid()
    # if not os.path.isdir('html_logs'):
    #     os.mkdir('html_logs')
    if not os.path.isdir('data'):
        os.mkdir('data')
    start_day = start_date = dt.datetime.strptime(start_date, DATE_FORMAT)
    end_date = dt.datetime.strptime(end_date, DATE_FORMAT)
    end_day = start_day + dt.timedelta(days=1)

    # day = dt.timedelta(days=1)
    day = dt.timedelta(days=1)

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36 OPR/44.0.2510.1218'
    }

    while end_day <= end_date:
        log_str = 'Load data from day %s - %s' % (start_day.strftime(DATE_FORMAT),
                                                     end_day.strftime(DATE_FORMAT))
        print('-' * len(log_str))
        print(log_str)
        print('-' * len(log_str))
        cookie = get_cookie(start_day, end_day)
        page_url = get_site_page_name(location)
        r = requests.get(BASE_URL + page_url, cookies=cookie, headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        global searchSessionId
        searchSessionId = soup.find('input', {'name': 'searchSessionId'})['value']
        print('Got %d...' % r.status_code)
        # with open('html_logs/%s_%s_%s.html' % (location,
        #                                        start_day.strftime('%d-%m-%Y'),
        #                                        end_day.strftime('%d-%m-%Y')), 'wt') as outf:
        #     outf.write(r.text)
        handle_data(r.text, location, start_date, end_date, start_day, end_day)
        print('Page parsed!')
        for pg_num, link in enumerate(get_other_pages(r.text), start=2):
            print('Loading page %d. Link: %s' % (pg_num, BASE_URL+link))
            time.sleep(timeout)
            r = requests.get(BASE_URL + link, cookies=cookie, headers=headers)
            print('Got %d...' % r.status_code)
            # with open('html_logs/%s_%s_%s__%d.html' % (location,
            #                                            start_day.strftime('%d-%m-%Y'),
            #                                            end_day.strftime('%d-%m-%Y'),
            #                                            pg_num), 'wt') as outf:
            #     outf.write(r.text)
            handle_data(r.text, location, start_date, end_date, start_day, end_day)
            print('Page parsed!')

        start_day += day
        end_day += day


if __name__ == '__main__':
    optlist, _ = getopt.getopt(sys.argv[1:], 'l:s:e:', ["location=", "stratdate=", "enddate="])
    for opt in optlist:
        if opt[0] in ('-l', '--location'):
            location = opt[1]
        elif opt[0] in ('-s', '--startdate'):
            start_date = opt[1]
        elif opt[0] in ('-e', '--enddate'):
            end_date = opt[1]
    if not all((location, start_date, end_date)):
        print('Usage: -l <location> -s <start date> -e <end date>')
        exit(-1)
    main(location, start_date, end_date)
