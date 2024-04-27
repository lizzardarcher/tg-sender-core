import datetime
import traceback
import utils.djangoORM
from time import sleep
from spambotapp.models import Account, Bot, TGAdmin, Chat, GeneralSettings, Message, AccountLogging
from pyrogram import Client
import logging
import os


logging.basicConfig(level=logging.WARNING)


def clear():
    accs = Account.objects.filter(status=True, is_spam_active=False)
    chats = Chat.objects.all()
    """ Проход по аккаунтам """
    for acc in accs:
        api_id = acc.api_id
        api_hash = acc.api_hash
        phone = acc.phone

        client = Client(
            name=f'{acc.session_for_chat}',
            api_id=api_id,
            api_hash=api_hash,
            phone_number=phone
        )
        client.start()
        """ Проход по группам """
        count = 1
        for chat in chats:
            chat_username = chat.username.split('/')[-1]
            try:
                client.leave_chat(chat_id=chat_username)
            except Exception as e:
                print(f"{str(count)}: ", chat, e)
            count += 1

        client.stop()

clear()