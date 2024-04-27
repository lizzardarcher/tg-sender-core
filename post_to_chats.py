import datetime
# import asyncio
# import aioconsole
import sys
from io import StringIO
import json
import traceback
import utils.djangoORM
from time import sleep
from spambotapp.models import Account, Bot, TGAdmin, Chat, GeneralSettings, Message, AccountLogging, ChannelToSubscribe
from pyrogram import Client
import logging
import os

# logging.basicConfig(level=logging.WARNING)

logging.basicConfig(filename='testpost.log', level=logging.WARNING)

"""
* Frequent ERRORS 

400 USER_BANNED_IN_CHANNEL
401 USER_DEACTIVATED_BAN 
403 CHAT_WRITE_FORBIDDEN
403 CHAT_SEND_MEDIA_FORBIDDEN
420 SLOWMODE_WAIT_X
420 FLOOD_WAIT_X

"""


def activate_account(acc_id: int):
    acc = Account.objects.get(id_account=acc_id)
    api_id = str(acc.api_id)
    api_hash = acc.api_hash
    session = acc.session
    phone = acc.phone
    name = f'{session}_spam_to_chat'
    print(api_id, api_hash, phone)
    app = Client(name=name, api_id=api_id, api_hash=api_hash,
                 device_model="iPhone 11 Pro",
                 system_version="16.1.2",
                 app_version="11.2",
                 lang_code="en")
    print('app ready to go')
    app.connect()
    print('app connected')
    sent_code = app.send_code(phone)
    print('code sent')
    while True:
        sms_code = Account.objects.get(id_account=acc_id).sms_code
        if sms_code:
            print('SMS is: ', sms_code)
            break
        else:
            print('waiting SMS')
            sleep(4)
    print('Trying to sing in')
    app.sign_in(phone, sent_code.phone_code_hash, sms_code)
    print('signed_in success')
    app.disconnect()
    # app.stop()
    print('app disconnected')
    Account.objects.filter(id_account=acc_id).update(sms_code='', signed_in=True, session_for_chat=name)
    print('Activated successful')
    os.system('systemctl restart autoanswering.service')


def post_to_chats():
    accs = Account.objects.filter(account_enabled=True, status=True, is_spam_active=True).order_by('-session_for_chat')
    chats = Chat.objects.filter(is_active=True)
    delay = int(GeneralSettings.objects.all()[0].general_delay)

    """ Проход по аккаунтам """
    for acc in accs:
        acc_id = acc.id_account
        # session = acc.session
        api_id = acc.api_id
        api_hash = acc.api_hash
        phone = acc.phone
        print(acc.session_for_chat)

        try:

            """ Если нет сессии для чатов, то создаём её"""
            if not acc.session_for_chat:
                print('No session for account')
                activate_account(acc_id)
                sleep(3)
                break

            """ Активируем клиент """
            client = Client(
                name=f'{acc.session_for_chat}',
                api_id=api_id, api_hash=api_hash,
                device_model="iPhone 11 Pro",
                system_version="16.1.2",
                app_version="11.2",
                lang_code="en")
            client.start()

            """ Проход по группам """
            for chat in chats:
                spam_active = Account.objects.filter(status=True, is_spam_active=True)
                if not spam_active:
                    break
                chat_id = chat.id
                chat_username = chat.username.split('/')[-1]

                """ Удаляем предыдущее сообщение, если дозволено"""
                if chat.is_del_mes_available:
                    try:
                        message = Message.objects.filter(chat=chat_id, account=acc_id, is_deleted=False).last()
                        m_id = message.id
                        message_to_delete = message.message_id
                        client.delete_messages(chat_username, message_to_delete)
                        Message.objects.filter(id=m_id).update(is_deleted=True)
                    except Exception as e:
                        print(e)
                        print(traceback.format_exc())

                """ 
                    Текст = текст.аккаунт, если нет, то текст.чат, если нет, то текст.общий 
                    Удаляем Emoji при необходимости
                """
                text = acc.common_text
                if not text:
                    text = Chat.objects.get(id=chat_id).text
                    if not text: text = GeneralSettings.objects.get(pk=1).general_text
                if not chat.is_emoji_allowed:
                    import re
                    emoji_pattern = re.compile("["
                                               u"\U0001F600-\U0001F64F"  # emoticons
                                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                               "]+", flags=re.UNICODE)
                    text = emoji_pattern.sub(r'', text)  # no emoji

                """ Присоединяемся к чату, если необходимо """
                to_subscribe = ChannelToSubscribe.objects.all()
                for _ in to_subscribe:
                    channel = _.username.split('/')[-1]
                    try:
                        client.join_chat(chat_id=channel)
                        client.archive_chats(chat_ids=channel)
                        sleep(0.9)
                    except Exception as e:
                        print(e)
                        # print(traceback.format_exc())
                        sleep(0.1)
                try:
                    client.join_chat(chat_id=chat_username)
                    client.archive_chats(chat_ids=chat_username)
                    sleep(1.5)
                except Exception as e:
                    print(e)
                    # print(traceback.format_exc())
                    sleep(4.1)

                """ Отправляем сообщение """
                try:
                    res = client.send_message(chat_id=chat_username, text=text)
                    jsn = json.loads(str(res))
                    sleep(7.7)

                    """ Записываем сообщение в базу """
                    account_obj = Account.objects.filter(id_account=jsn['from_user']['id'])[0]
                    chat_obj = Chat.objects.filter(id=chat_id)[0]
                    Message.objects.create(message_id=jsn['id'], account=account_obj,
                                           datetime=datetime.datetime.now(), chat=chat_obj)
                    AccountLogging.objects.create(log_level='Info', account=acc,
                                                  message='MESSAGE SENT',
                                                  datetime=datetime.datetime.now(), chat=chat)
                except Exception as e:
                    print(traceback.format_exc())
                    if '401 USER_DEACTIVATED_BAN' in traceback.format_exc():
                        Account.objects.filter(id_account=acc_id).update(status=False)
                        AccountLogging.objects.create(log_level='Fatal', account=acc,
                                                      message='401 USER_DEACTIVATED_BAN',
                                                      datetime=datetime.datetime.now(), chat=chat)
                    elif '400 USER_BANNED_IN_CHANNEL' in traceback.format_exc():
                        AccountLogging.objects.create(log_level='Warning', account=acc,
                                                      message='400 USER_BANNED_IN_CHANNEL',
                                                      datetime=datetime.datetime.now(), chat=chat)
                        chat.is_user_banned.add(Account.objects.get(id_account=acc_id))
                        break
                    elif '403 CHAT_WRITE_FORBIDDEN' in traceback.format_exc():
                        AccountLogging.objects.create(log_level='Warning', account=acc,
                                                      message='403 CHAT_WRITE_FORBIDDEN',
                                                      datetime=datetime.datetime.now(), chat=chat)
                    elif '403 CHAT_SEND_MEDIA_FORBIDDEN' in traceback.format_exc():
                        AccountLogging.objects.create(log_level='Warning', account=acc,
                                                      message='403 CHAT_SEND_MEDIA_FORBIDDEN',
                                                      datetime=datetime.datetime.now(), chat=chat)
                    elif '420 SLOWMODE_WAIT_X' in traceback.format_exc():
                        AccountLogging.objects.create(log_level='Warning', account=acc,
                                                      message='420 SLOWMODE_WAIT_X',
                                                      datetime=datetime.datetime.now(), chat=chat)
                    elif '403 CHAT_SEND_PLAIN_FORBIDDEN' in traceback.format_exc():
                        AccountLogging.objects.create(log_level='Warning', account=acc,
                                                      message='403 CHAT_SEND_PLAIN_FORBIDDEN',
                                                      datetime=datetime.datetime.now(), chat=chat)
                    elif '400 TOPIC_CLOSED' in traceback.format_exc():
                        AccountLogging.objects.create(log_level='Warning', account=acc,
                                                      message='400 TOPIC_CLOSED',
                                                      datetime=datetime.datetime.now(), chat=chat)
                    elif '420 FLOOD_WAIT_X' in traceback.format_exc():
                        sec = traceback.format_exc().split('A wait of')[-1].split('seconds')[0]
                        msg = f'Wait {sec} seconds'
                        AccountLogging.objects.create(log_level='Warning', account=acc,
                                                      message=msg,
                                                      datetime=datetime.datetime.now(), chat=chat)
            sleep(0.01)
            client.stop()
            sleep(1800)
            # sleep(delay * 60)
        except Exception as e:
            print(e)
            print(traceback.format_exc())


while True:
    try:
        accounts = Account.objects.filter(status=True, is_spam_active=True)
        if accounts:
            post_to_chats()
            sleep(5)
        else:
            sleep(30)
    except KeyboardInterrupt:
        print(traceback.format_exc())
        if 'database is locked' in traceback.format_exc():
            sleep(0.1)
        else:
            sleep(30)
