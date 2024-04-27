import traceback

import requests
from bs4 import BeautifulSoup


def get_chat_info(chat_link):
    try:
        url = chat_link
        r = requests.get(url=url).text
        soup = BeautifulSoup(r, 'lxml')
        # image = soup.find("img", {"class": "tgme_page_photo_image"})['src']
        title = soup.find("span", {"dir": "auto"}).text
        raw_subscribers = soup.find("div", {"class": "tgme_page_extra"}).text
        subscribers = ''
        if 'sub' in raw_subscribers:
            for i in raw_subscribers.split(' '):
                if 'sub' not in i:
                    subscribers += i
        elif 'members' in raw_subscribers:
            subscribers = raw_subscribers.split(' members')[0].replace(' ', '')
        subscribers = int(subscribers)
        # print('Ссылка на изображение', image)
        # print('Название чата:', title)
        # print('Количество подписчиков:', subscribers)
    except:
        print(traceback.format_exc())
        # image = ''
        title = ''
        subscribers = 0
    return title, subscribers


def get_bot_info(chat_link):
    try:
        url = chat_link
        r = requests.get(url=url).text
        soup = BeautifulSoup(r, 'lxml')
        title = soup.find("span", {"dir": "auto"}).text
    except:
        title = ''
    return title
