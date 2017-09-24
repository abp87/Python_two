import csv
import re
import datetime as dt
import os

from bs4 import BeautifulSoup

TA_URL = 'https://www.tripadvisor.com'
hotel_num_pattern = re.compile(r'hotel_(\d+)')
locality_id_pattern = re.compile(r'-g(\d+)-')
hotel_ids = []


def handle_data(page: str, location: str, start_date: dt.datetime, end_date: dt.datetime,
                checkin: dt.datetime, checkout: dt.datetime):
    hotels_fn = 'data/{}_hotels_{}_{}.csv'.format(location, start_date.strftime('%m%d%Y'),
                                                  end_date.strftime('%m%d%Y'))
    prices_fn = 'data/{}_prices_{}_{}.csv'.format(location, start_date.strftime('%m%d%Y'),
                                                  end_date.strftime('%m%d%Y'))
    first = not os.path.isfile(hotels_fn)

    soup = BeautifulSoup(page, 'html.parser')
    with open(hotels_fn, 'at') as outf:
        with open(prices_fn, 'at') as outf2:
            fieldnames_hot = ['hotel_id', 'hotel_name', 'hotel_url', 'locality_id',
                              'review_count', 'TA_rating', 'TA_rank', 'hotel_features']
            csvwr = csv.DictWriter(outf, fieldnames=fieldnames_hot)
            fieldnames_pr = ['hotel_id', 'acq_date', 'checkin_date', 'checkout_date',
                             'provider', 'offerclient', 'vendorname', 'pernight']
            csvwr2 = csv.DictWriter(outf2, fieldnames=fieldnames_pr)
            if first:
                csvwr.writeheader()
                csvwr2.writeheader()
            hotels = soup.find('div', id='BODYCON') \
                .find_all('div', {'id': re.compile(r'hotel_(\d+)')})
            for i, hotel in enumerate(hotels, start=1):
                print('Handling %d hotel...' % i)
                row = {
                    'hotel_id': hotel_num_pattern.search(hotel['id']).group(1),
                    'hotel_name': hotel.find('div', {'class': 'listing'}).a.contents[0], #was {'class': 'listing_title'}
                    'hotel_url': TA_URL + hotel.find('div', {'class': 'listing'}).a['href'] #was listing_title
                }
                row['locality_id'] = locality_id_pattern.search(row['hotel_url']).group(1)
                try:
                    row['review_count'] = re.findall(r'\d+',
                                                     hotel.find('div', {'class': 'rtofimg'})
                                                     .find('span', {'class': 'reviewCount'})
                                                     .a.contents[0].replace('\xa0', ''))[0]
                    row['TA_rating'] = re.findall(r'\d+',
                                                  hotel.find('div', {'class': 'rtofimg'})
                                                  .find('div', {'class': 'slim_ranking'})
                                                  .contents[0].replace('\xa0', ''))[0]
                    row['TA_rank'] = hotel.find('div', {'class': 'rtofimg'}) \
                        .find('div', {'class': 'bubbleRating'}).div.span['content']
                except AttributeError:
                    row['review_count'] = ''
                    row['TA_rating'] = ''
                    row['TA_rank'] = ''
                hotel_features = []
                for li in hotel.find('div', {'class': 'rtofimg'}) \
                        .find('div', {'class': 'amenities_list'}).div.ul.children:
                    hotel_features.append(li.find('div', {'class': 'label'}).contents[0])
                row['hotel_features'] = ', '.join(hotel_features)
                if row['hotel_id'] not in hotel_ids:
                    csvwr.writerow(row)
                    hotel_ids.append(row['hotel_id'])
                try:
                    offer_divs = hotel.find('div', {'id': re.compile(r'VIEW_ALL_DEALS_\d+')}) \
                        .find('div', {'data-prwidget-name': 'meta_view_all_text_links_declutter'}).children
                except AttributeError:
                    continue
                for j, off in enumerate(offer_divs, start=1):
                    print('Offer %d' % j)
                    if 'data-pernight' in off.attrs:
                        row2 = {
                            'hotel_id': row['hotel_id'],
                            'acq_date': dt.date.today().strftime('%m/%d/%Y'),
                            'checkin_date': checkin.strftime('%m/%d/%Y'),
                            'checkout_date': checkout.strftime('%m/%d/%Y'),
                            'provider': off['data-provider'],
                            'offerclient': off['data-offerclient'],
                            'vendorname': off['data-vendorname'],
                            'pernight': off['data-pernight']
                        }
                        csvwr2.writerow(row2)


if __name__ == '__main__':
    with open('html_logs/Dubai_02-07-2017_03-07-2017__16.html') as fp:
        handle_data(fp, 'test', dt.datetime.now(), dt.datetime.now())
