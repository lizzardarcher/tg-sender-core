import traceback

from telebot import TeleBot
import os
import utils.djangoORM
from time import sleep
from spambotapp.models import Account, Bot, TGAdmin
from pyrogram import Client
import utils.msg as MSG

TOKEN = Bot.objects.get(pk=1).token
bot = TeleBot(TOKEN, parse_mode='HTML', disable_web_page_preview=True)


def activate_account(acc_id: int):
    acc = Account.objects.get(id_account=acc_id)
    api_id = str(acc.api_id)
    api_hash = acc.api_hash
    phone = acc.phone
    name = 'sessions/' + api_id + api_hash
    # print(api_id, api_hash, phone)
    client = Client(name=name, api_id=api_id, api_hash=api_hash,
                device_model="iPhone 11 Pro",
                system_version="16.1.2",
                app_version="11.2",
                lang_code="en")
    # print('client ready to go')
    client.connect()
    # print('client connected')
    sent_code = client.send_code(phone)
    # print('code sent')
    while True:
        sms_code = Account.objects.get(id_account=acc_id).sms_code
        if sms_code:
            # print('SMS is: ', sms_code)
            Account.objects.filter(id_account=acc_id).update(sms_code='')
            break
        else:
            # print('waiting SMS')
            sleep(4)
    # print('Trying to sing in')
    signed_in = client.sign_in(phone, sent_code.phone_code_hash, sms_code)
    # print('signed_in success')
    client.disconnect()
    # print('client disconnected')
    Account.objects.filter(id_account=acc_id).update(signed_in=True, session=name)
    # print('Activated successful')
    os.system('systemctl restart autoanswering.service')


def check_all_acounts(chat_id):
    os.system('systemctl stop autoanswering.service')
    sleep(3)
    try:
        accs = Account.objects.filter(account_enabled=True)
        for acc in accs:
            acc_id = acc.id_account
            session = acc.session
            try:
                with Client(name=session) as client:
                    client.send_message('me', 'Checking account from bot :: result :: Ready to go!')
                bot.send_message(chat_id=chat_id, text=MSG.check_account_success.format(str(acc_id)))
            except:
                bot.send_message(chat_id=chat_id, text=MSG.check_account_fail.format(str(acc_id)))

    except:
        print(traceback.format_exc())
    os.system('systemctl start autoanswering.service')


# todo Костыль, надо переделать через БД
while True:
    try:
        with open('flag.txt', 'r') as file:
            flag = file.read()
            if flag:
                acc_id = int(flag.split(':')[-1])

                try:
                    activate_account(acc_id)
                except:
                    print(traceback.format_exc())

                with open('flag.txt', 'w') as file:
                    flag = file.write()
            else:
                # print('No flag')
                sleep(5)
        with open('flag2.txt', 'r') as file:
            chat_id = file.read()
            if chat_id:
                try:
                    check_all_acounts(chat_id)
                except:
                    print(traceback.format_exc())
                with open('flag2.txt', 'w') as file:
                    chat_id = file.write()
            else:
                # print('No flag 2')
                sleep(5)
    except:
        print(traceback.format_exc())
