import asyncio
from time import sleep
import datetime
import json
import traceback
import logging
import re
from pyrogram import Client, compose, idle, filters
from pyrogram.handlers import MessageHandler

import utils.djangoORM
from spambotapp.models import Account, Bot, TGAdmin, Chat, GeneralSettings, \
    Message, MasterAccount, ChatMaster, ChannelToSubscribe
from spambotapp.models import Client as Tg_client

logging.basicConfig(level=logging.FATAL)

# todo systemd MaxRunTimeSec 600

async def activate_account(acc_id: int):
    acc = Account.objects.get(id_account=acc_id)
    api_id = str(acc.api_id)
    api_hash = acc.api_hash
    session = acc.session
    phone = acc.phone
    name = f'{session}spam_to_chat'
    print(api_id, api_hash, phone)
    client = Client(name=name, api_id=api_id, api_hash=api_hash,
                    device_model="iPhone 13 Pro Max",
                    system_version="14.8.1",
                    app_version="8.4", lang_code="en")
    print('client ready to go')
    await client.connect()
    print('client connected')
    sent_code = await client.send_code(phone)
    print('code sent')
    # Account.objects.filter(id_account=acc_id).update(sms_code='')
    while True:
        sms_code = Account.objects.get(id_account=acc_id).sms_code
        if sms_code:
            print('SMS is: ', sms_code)
            # clear sms_code
            Account.objects.get(id_account=acc_id).sms_code = ''
            break
        else:
            print('waiting SMS')
            sleep(4)
    print('Trying to sing in')
    signed_in = await client.sign_in(phone, sent_code.phone_code_hash, sms_code)
    print('signed_in success')
    await client.disconnect()
    print('client disconnected')
    Account.objects.filter(id_account=acc_id).update(signed_in=True, session=name)
    print('Activated successful')
    os.system('systemctl restart autoanswering.service')

async def main():
    """ Автоответчик """

    """ Пул аккаунтов """
    accs = Account.objects.filter(account_enabled=True, status=True, is_auto_answering_active=True)
    master = MasterAccount.objects.filter(is_master=True).last()
    slave = MasterAccount.objects.filter(is_duplicate=True).last()
    # slave = MasterAccount.objects.filter(is_master=True).last()
    # master = MasterAccount.objects.filter(is_duplicate=True).last()

    for i in accs:
        print(i)
    """ Пул сессий """
    apps = [Client(x.session) for x in accs]

    """ Активируем клиенты pyrogram с помощью compose() """
    for app in apps:
        # print(app.name)
        @app.on_message(filters.reply)
        async def reply_(client, message):
            if str(message.from_user.id) == str(master.id_account):
                """ Пересыл через реплай """
                """ Forward from master """
                try:
                    print('message.reply_to_message.forward_from.id', message.reply_to_message.forward_from.id)
                    await client.send_message(chat_id=message.reply_to_message.forward_from.id, text=message.text)
                except:
                    print(traceback.format_exc())
                    # await client.send_message(chat_id=message.reply_to_message.forward_from.id, text=message.text)
                    # print(f'No ID\n{message}')
                """ Forward to slave """
                title = message.reply_to_message.chat.title
                chat_id = ChatMaster.objects.filter(title=title, comment='Duplicate').last()
                await client.forward_messages(chat_id=chat_id.id, from_chat_id=message.chat.id, message_ids=message.id)

        @app.on_message(filters.text & filters.private or filters.text & filters.private & filters.reply)
        async def answer_(client, message):
            if str(message.from_user.id) != str(master.id_account):
                if 'Код для входа' in message.text or 'Login code' in message.text:
                    code = re.findall('\d+', message.text)[0]
                    r = await client.get_me()
                    print(r.id)
                    print(f'Code :: {code}')
                    a = Account.objects.filter(id_account=int(r.id)).update(sms_code=code)
                    print(a)
                else:

                    """
                        1. Пересыл сообщений на мастер аккаунт
                        2. Аккаунт отвечает клиенту 1 раз (по идее) и добавляем его в базу.
                    """

                    get_me = await client.get_me()
                    tg_cli = Tg_client.objects.filter(user_id=message.from_user.id)

                    """
                        * Ответ пользователю
                        * Создание объекта клиента
                    """
                    if not tg_cli:
                        text = Account.objects.filter(session=client.name)[0].auto_answering_text
                        if not text:
                            text = GeneralSettings.objects.get(pk=1).general_auto_answering
                        await asyncio.sleep(10)
                        await client.send_message(message.chat.id, text)
                        user_id = message.from_user.id
                        username = message.from_user.username
                        first_name = message.from_user.first_name
                        if not username: username = str(first_name)
                        last_name = message.from_user.last_name
                        Tg_client.objects.create(user_id=user_id, username=username, first_name=first_name, last_name=last_name)

                    tg_cli = Tg_client.objects.filter(user_id=message.from_user.id)
                    # Название группы общее у мастера и дубликата
                    title = f'Чат с {tg_cli.last().username.split("/")[-1]} от {get_me.username}'

                    """  Создание Чата в мастере, если нет """
                    groups = ChatMaster.objects.filter(title=title)
                    master_app = Client(master.session)
                    await master_app.start()

                    if not groups:
                        if tg_cli.last().username.split("/")[-1].lower() != 'chatkeeperbot':
                            group = await master_app.create_group(title=title, users=[get_me.username])
                            ChatMaster.objects.create(id=group.id, title=group.title, comment='Master')

                    groups = ChatMaster.objects.filter(title=title, comment='Master')
                    group_id = groups.last().id
                    await master_app.stop()
                    await asyncio.sleep(1)

                    """ Пересыл сообщений в чат на мастер аккаунт """
                    await client.forward_messages(chat_id=group_id, from_chat_id=message.chat.id, message_ids=message.id)

                    """  Создание Чата в дубликате, если нет """
                    slave_app = Client(slave.session)
                    await slave_app.start()

                    groups = ChatMaster.objects.filter(title=title, comment='Duplicate')
                    if not groups:
                        group = await slave_app.create_group(title=title, users=[get_me.username])
                        ChatMaster.objects.create(id=group.id, title=group.title, comment='Duplicate')

                    groups = ChatMaster.objects.filter(title=title, comment='Duplicate')
                    group_id = groups.last().id
                    await slave_app.stop()
                    await asyncio.sleep(1)

                    """ Пересыл сообщений в чат на дубликат аккаунт """
                    await client.forward_messages(chat_id=group_id, from_chat_id=message.chat.id, message_ids=message.id)

    await compose(apps)


if __name__ == '__main__':
    asyncio.run(main())
