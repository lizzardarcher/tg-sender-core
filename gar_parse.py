from time import sleep

import requests
from bs4 import BeautifulSoup
url = 'https://ru.tradingview.com/symbols/USDTRUB/'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
r = requests.get(url=url, headers=headers, timeout=10)

print(r)
soup = BeautifulSoup(r.text, 'lxml')
price_1 = soup.find('span', {"class": 'last-JWoJqCpY js-symbol-last'})
print(price_1)