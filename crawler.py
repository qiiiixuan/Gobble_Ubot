import pandas as pd
import requests
from bs4 import BeautifulSoup
          
dataset_id = 'd_1f0313499a17075d13aae6ed3e825bc6'
url = 'https://api-open.data.gov.sg/v1/public/api/datasets/' + dataset_id + '/poll-download'
        
response = requests.get(url)
json_data = response.json()
if json_data['code'] != 0:
    print(json_data['errMsg'])
    exit(1)

url = json_data['data']['url']
restaurantList = requests.get(url).json()['features']

restaurantDataFrame = pd.DataFrame({
    'Company': [],
    'Name': [],
    'Address': [],
})

length = len(restaurantList)
for index, restaurant in enumerate(restaurantList):
    text = restaurant['properties']['Description']

    soup = BeautifulSoup(text, 'html.parser')
    description = soup.find_all('td')

    company = description[0].get_text()
    name = description[6].get_text()
    block = description[1].get_text()
    street = description[2].get_text()
    unit = description[3].get_text()
    unit = '0' + unit if unit.isnumeric() and int(unit) < 10 else unit
    postal = description[4].get_text()
    postal = '0' + postal if postal.isnumeric() and int(postal) < 100000 else postal
    level = description[7].get_text()
    level = '0' + level if level.isnumeric() and int(level) < 10 else level
    levelUnit = ' #' + level + '-' + unit if level != '' and unit != '' else ''
    address = block + ' ' + street + levelUnit + ', SINGAPORE ' + postal

    restaurantData = pd.DataFrame({
        'Company': [company],
        'Name': [name],
        'Address': [address],
    })

    restaurantDataFrame = pd.concat([restaurantDataFrame, restaurantData], ignore_index=True)

    if (index + 1) % 1000 == 0: 
        print("Restaurants Scraped: " + str(index + 1) + "/" + str(length))

restaurantDataFrame.to_excel('Restaurants.xlsx', sheet_name='Restaurant List')