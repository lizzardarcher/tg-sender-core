import datetime
import json
import traceback
import utils.djangoORM
from time import sleep
from spambotapp.models import Account, Bot, TGAdmin, Chat, GeneralSettings, Message, AccountLogging
from spambotapp.models import Client as Tg_client
from pyrogram import Client
import logging
import os
logging.basicConfig(level=logging.WARNING)

"""
* Frequent ERRORS 

400 USER_BANNED_IN_CHANNEL
401 USER_DEACTIVATED_BAN 
403 CHAT_WRITE_FORBIDDEN
403 CHAT_SEND_MEDIA_FORBIDDEN
420 SLOWMODE_WAIT_X

"""


def post_to_lks():
    os.system('systemctl stop autoanswering.service')
    accs = Account.objects.filter(account_enabled=True, status=True, is_spam_lk_active=True)
    clients = Tg_client.objects.filter(is_spam_active=True)
    # delay = int(GeneralSettings.objects.all()[0].general_delay)
    print(accs, clients)
    cl = None
    """ Проход по аккаунтам """
    for acc in accs:
        acc_id = acc.id_account
        session = acc.session
        api_id = acc.api_id
        api_hash = acc.api_hash
        try:
            with Client(name=session,
                        api_id=api_id,
                        api_hash=api_hash,
                        device_model="iPhone 13 Pro Max",
                        system_version="14.8.1",
                        app_version="8.4",
                        lang_code="en") as client:

                """ Проход по клиентам """
                for cli in clients:
                    cl = cli
                    """ Текст = текст.аккаунт, если нет, то текст.общий """
                    text = acc.common_text
                    if not text:
                        text = GeneralSettings.objects.get(pk=1).general_text

                    try:
                        """ Отправляем сообщение """
                        client.send_message(chat_id=cli.user_id, text=text)

                        """ Записываем сообщение в базу """
                        # account_obj = Account.objects.get(id_account=jsn['chat']['id'])
                        AccountLogging.objects.create(log_level='Info', account=acc,
                                                      message='Рассылка. Отправлено в ЛС успешно',
                                                      datetime=datetime.datetime.now(), client=cli)
                        break
                    except Exception as e:
                        print(traceback.format_exc())
                sleep(0.01)
        except:
            print(traceback.format_exc())
            try:
                if '401 USER_DEACTIVATED_BAN' in traceback.format_exc():
                    Account.objects.filter(id_account=acc_id).update(status=False)
                    AccountLogging.objects.create(log_level='Fatal', account=acc,
                                                  message='401 USER_DEACTIVATED_BAN',
                                                  datetime=datetime.datetime.now(), client=cl)
                elif '400 USER_BANNED_IN_CHANNEL' in traceback.format_exc():
                    AccountLogging.objects.create(log_level='Warning', account=acc,
                                                  message='400 USER_BANNED_IN_CHANNEL',
                                                  datetime=datetime.datetime.now(), client=cl)
                elif '403 CHAT_WRITE_FORBIDDEN' in traceback.format_exc():
                    AccountLogging.objects.create(log_level='Warning', account=acc,
                                                  message='403 CHAT_WRITE_FORBIDDEN',
                                                  datetime=datetime.datetime.now(), client=cl)
                elif '403 CHAT_SEND_MEDIA_FORBIDDEN' in traceback.format_exc():
                    AccountLogging.objects.create(log_level='Warning', account=acc,
                                                  message='403 CHAT_SEND_MEDIA_FORBIDDEN',
                                                  datetime=datetime.datetime.now(), client=cl)
                elif '420 SLOWMODE_WAIT_X' in traceback.format_exc():
                    AccountLogging.objects.create(log_level='Warning', account=acc,
                                                  message='420 SLOWMODE_WAIT_X',
                                                  datetime=datetime.datetime.now(), client=cl)
            except:
                print(traceback.format_exc())
    os.system('systemctl start autoanswering.service')


while True:
    try:
        accs = Account.objects.filter(status=True, is_spam_lk_active=True)
        if accs:
            post_to_lks()
            Account.objects.filter(status=True, is_spam_lk_active=True).update(is_spam_lk_active=False)
            sleep(5)
        else:
            sleep(30)
    except KeyboardInterrupt:
        print(traceback.format_exc())
        sleep(30)
