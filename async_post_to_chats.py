import datetime
import random
import string
import asyncio
import sys
import threading
from io import StringIO
import json
import traceback
import utils.djangoORM
from time import sleep
from spambotapp.models import Account, Bot, TGAdmin, Chat, GeneralSettings, Message, AccountLogging, ChannelToSubscribe
from pyrogram import Client
from pyrogram.enums import ParseMode
import logging
import os

# logging.basicConfig(level=logging.WARNING)

logging.basicConfig(filename='testpost.log', level=logging.WARNING)


async def activate_account(acc_id: int):
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
    await app.connect()
    print('app connected')
    sent_code = await app.send_code(phone)
    print('code sent')
    while True:
        sms_code = Account.objects.get(id_account=acc_id).sms_code
        if sms_code:
            print('SMS is: ', sms_code)
            break
        else:
            print('waiting SMS')
            await asyncio.sleep(4)
    print('Trying to sing in')
    await app.sign_in(phone, sent_code.phone_code_hash, sms_code)
    print('signed_in success')
    await app.disconnect()
    # app.stop()
    print('app disconnected')
    Account.objects.filter(id_account=acc_id).update(sms_code='', signed_in=True, session_for_chat=name)
    print('Activated successful')
    os.system('systemctl restart autoanswering.service')


async def post_to_chats(acc_id):
    for _ in range(10000):
        await asyncio.sleep(random.randint(1, 30))
        acc = Account.objects.filter(id_account=acc_id)[0]
        chats = Chat.objects.filter(is_active=True).order_by('?')
        delay = int(GeneralSettings.objects.all()[0].general_delay)

        # random.shuffle(chats)
        # print(chats)

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
                await activate_account(acc_id)
                await asyncio.sleep(3)
            else:
                """ Активируем клиент """
                client = Client(
                    name=f'{acc.session_for_chat}',
                    api_id=api_id, api_hash=api_hash,
                    device_model="iPhone 11 Pro",
                    system_version="16.1.2",
                    app_version="11.2",
                    lang_code="en")
                await client.start()

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
                            await client.delete_messages(chat_username, message_to_delete)
                            Message.objects.filter(id=m_id).update(is_deleted=True)
                        except Exception as e:
                            print(e)
                            # print(traceback.format_exc())

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
                            await client.join_chat(chat_id=channel)
                            await client.archive_chats(chat_ids=channel)
                            await asyncio.sleep(0.9)
                        except Exception as e:
                            print(e)
                            # print(traceback.format_exc())
                            await asyncio.sleep(0.1)
                    try:
                        await client.join_chat(chat_id=chat_username)
                        await client.archive_chats(chat_ids=chat_username)
                        await asyncio.sleep(1.5)
                    except Exception as e:
                        print(e)
                        # print(traceback.format_exc())
                        await asyncio.sleep(4.1)

                    """ Отправляем сообщение """
                    def random_string(letter_count, digit_count):
                        str1 = ''.join((random.choice(string.ascii_letters) for x in range(letter_count)))
                        str1 += ''.join((random.choice(string.digits) for x in range(digit_count)))

                        sam_list = list(str1)  # it converts the string to list.
                        random.shuffle(sam_list)  # It uses a random.shuffle() function to shuffle the string.
                        final_string = ''.join(sam_list)
                        return f'\n||ID: {final_string}||'
                    text = text+random_string(6, 6)
                    try:
                        res = await client.send_message(chat_id=chat_username, text=text, parse_mode=ParseMode.MARKDOWN)
                        jsn = json.loads(str(res))
                        await asyncio.sleep(7.7)
                        print('Message sent')
                        """ Записываем сообщение в базу """
                        account_obj = Account.objects.filter(id_account=jsn['from_user']['id'])[0]
                        chat_obj = Chat.objects.filter(id=chat_id)[0]
                        Message.objects.create(message_id=jsn['id'], account=account_obj,
                                               datetime=datetime.datetime.now(), chat=chat_obj)
                        AccountLogging.objects.create(log_level='Info', account=acc,
                                                      message='MESSAGE SENT',
                                                      datetime=datetime.datetime.now(), chat=chat)
                    except Exception as e:
                        # print(traceback.format_exc())
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
                await asyncio.sleep(0.01)
                await client.stop()
                await asyncio.sleep(delay * 60)
        except Exception as e:
            print(e)
            print(traceback.format_exc())


if __name__ == '__main__':
    accounts = Account.objects.filter(account_enabled=True, status=True, is_spam_active=True)

    loop = asyncio.get_event_loop()
    for account in accounts:
        acc_id = account.id_account
        loop.create_task(post_to_chats(acc_id))
    loop.run_forever()
