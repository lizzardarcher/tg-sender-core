import asyncio
from time import sleep
import datetime
import json
import traceback
import logging

from pyrogram import Client, compose, idle, filters
from pyrogram.handlers import MessageHandler

import utils.djangoORM
from spambotapp.models import Account, Bot, TGAdmin, Chat, GeneralSettings, Message, MasterAccount, ChatMaster
from spambotapp.models import Client as Tg_client

logging.basicConfig(level=logging.WARNING)


async def main():
    """ Автоответчик """
    master = MasterAccount.objects.filter(is_master=True).last()
    master_app = Client(master.session)

    async with master_app:

        @master_app.on_message(filters.chat & filters.incoming)
        async def answer(client, message):
            await master_app.send_message(chat_id=message.chat.id, text=message.text)


if __name__ == '__main__':
    asyncio.run(main())
