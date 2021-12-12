from time import strftime, sleep, perf_counter
from bs4 import BeautifulSoup
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import ActionChains
import datetime
from collections import OrderedDict

webdriver_path = 'chromedriver.exe'
prop_url = 'https://www.propertyguru.com.sg/property-for-sale/'
price_regex = r'[1-9]{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})'
PAGE_MAX = 10

def main():
    # Get date and time for file labelling
    dt = datetime.datetime.now().strftime('%Y-%m-%d_%H.%M')
    
    # Get all property types
    with open('property_types.txt', 'r') as f:
        property_types = f.read().splitlines()
    
    # Initialise and go to website
    options = Options()
    # options.headless = True # Will trip bot detection
    
    # Init column and variable names
    columns_list = [
        'Project Name',
        'Location',
        'Type',
        'Price',
        'Size',
        'PSF',
        'Bed',
        'Bath',
        'Link',
        'Remarks'
    ]
    # Looking for these fields
    houses = {
        'proj_names': [],
        'proj_loc': [],
        'proj_type': [],
        'proj_price': [],
        # 'land_size': [],
        'floor_size': [],
        'psf': [],
        'beds': [],
        'baths': [],
        'link': [],
        'remarks': [],
    }
    
    # Get input parameters
    # custom_params = OrderedDict([
    #     ('Location', ''),
    #     ('Property Type', ''),
    # ])
    # print('Specify custom parameters. If none, press \'q\'.')
    # resp = ''
    # while resp != 'q':
    #     custom_params[0] = resp
    #     for num, k in enumerate(custom_params.keys()):
    #         print(f'{num+1} - {k}: {resp}')
    #     resp = input('> ')
    
    # Go to page
    page_range = [x for x in range(1, PAGE_MAX+1)]
    hometypes = []
    outer_time = perf_counter()
    for page in page_range:
        inner_time = perf_counter()
        print(f"Running for page {page}")
        # Get all the listing IDs
        driver = webdriver.Chrome(webdriver_path, options=options)
        driver.get(prop_url + str(page))
        content = driver.page_source
        soup = BeautifulSoup(content, 'lxml')
        listing_ids = [x['data-listing-id'] for x in soup.find_all('div', class_="alert hide hide-listing-alert")]
        
        # Start scraping
        for idx, listing_id in enumerate(listing_ids):
            # card_class = f'listing-card listing-id-{listing_id} listing-card-sale'
            # extra_card_info =  'listing-card-large turbo-listing'
            # listing_info = None
            # while listing_info is None:
            listing_info = soup.find(
                'div',
                class_=f'listing-card listing-id-{listing_id} listing-card-sale listing-card-large turbo-listing'
                )
                # card_class += extra_card_info
                # print(card_class)
                
            houses['proj_names'].append(listing_info.find('a', class_='nav-link').text)
            houses['proj_loc'].append(listing_info.find('span', attrs={'itemprop':'streetAddress'}).text)
            
            # Information is not at a fixed index
            remarks = ''
            info_bar = listing_info.find('ul', class_='listing-property-type')
            added_house_type = False
            for info in info_bar.contents:
                try:
                    if info.find('span').text in property_types:
                        home_type = info.find('span').text
                        hometypes.append(home_type)
                        houses['proj_type'].append(home_type)
                        added_house_type = True
                    else:
                        remarks += info.find('span').text + ', '
                except AttributeError:
                    # Newlines cause error
                    continue
            
            if not added_house_type:
                houses['proj_type'].append('Type NA')
            houses['remarks'].append(remarks)
            
            houses['proj_price'].append(listing_info.find('span', class_='price').text)
            house_features = listing_info.find('ul', class_='listing-features pull-left')
            size_psf = house_features.find_all('li', class_='listing-floorarea pull-left')
            houses['floor_size'].append(size_psf[0].text)
            
            try:
                houses['psf'].append(float(re.findall(price_regex, size_psf[1].text)[0].replace(',','')))
            except IndexError:
                house_price = float(listing_info.find('span', class_='price').text.replace(',', ''))
                print(re.findall(r'\d{1,5}', size_psf[0].text)[0])
                house_size = float(re.findall(r'\d{1,5}', size_psf[0].text)[0])
                houses['psf'].append(float(f'{house_price/house_size:.2f}'))
                
            houses['beds'].append(listing_info.find('span', {'class': ['bed', 'studio']}).text.strip())
            try:
                houses['baths'].append(int(listing_info.find('span', class_='bath').text.strip()))
            except:
                houses['baths'].append('N/A')
            houses['link'].append(listing_info.find('a', class_='nav-link')['href'])
        print(f'Time taken for page {page}: {perf_counter()-inner_time:.3f}s')
        driver.close()
        print(len(houses['proj_type']), idx+1, len(houses['proj_type']) == (idx+1))
        # listings = soup.find('div', class_=)
        
        # Click onto next page?
        # element = driver.find_element_by_xpath('//*[@id="search-results-container"]/div[2]/div[1]/div[2]/div[3]/section/div[3]/ul/li[3]/a')
        # action.move_to_element(element)
        # action.click()
        
        
    house_df = pd.DataFrame.from_dict(houses, orient='columns')
    house_df = house_df.rename(columns={var:newname for var, newname in zip(houses.keys(), columns_list)})
    house_df.to_excel(f'houses_{dt}.xlsx')
    tot_time = perf_counter() - outer_time
    print(f'Total running_time = {tot_time//60:.0f}min {tot_time%60:.0f}s')

if __name__ == '__main__':
    main()