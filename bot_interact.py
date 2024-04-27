import utils.djangoORM
import ast
import math
from time import sleep
import traceback
import logging
import os
from pyrogram import Client
from telebot import TeleBot, logger, types
import datetime
from spambotapp.models import Bot, Account, TGAdmin, Chat, GeneralSettings, Message
import utils.kb as KB
import utils.msg as MSG
import utils.handler as hd

TOKEN = Bot.objects.get(pk=1).token
bot = TeleBot(TOKEN, parse_mode='HTML', disable_web_page_preview=True)
# logger.setLevel(logging.DEBUG)
selected_accounts = []
selected_accounts_for_lk = []
web_admin_panel = 'http://91.222.239.242/admin'

@bot.message_handler(commands=['start'])
def start(message):
    admin_ids = [i.user_id for i in TGAdmin.objects.filter(user_id=message.from_user.id)]  # Получаем список ID админов
    if message.chat.type == 'private':
        if message.from_user.id in admin_ids:
            bot.send_message(chat_id=message.chat.id, text=MSG.start, reply_markup=KB.start_markup())
        else:
            bot.send_message(chat_id=message.chat.id, text=MSG.not_admin)


@bot.callback_query_handler(func=lambda call: True)
def callback_query_handlers(call):
    print('callback :: ', call.data)
    is_spam_active = Account.objects.filter(is_spam_active=True)
    accounts = [(account.id_account, account.username) for account in Account.objects.filter(status=True)]
    chats = [(chat.username, chat.id) for chat in Chat.objects.all()]
    admins = [(admin.username, admin.user_id) for admin in TGAdmin.objects.all()]
    admins_str = str(admins).replace("'", '').replace(']', '').replace('(', 'admin: ').replace(')', '').replace('[',
                                                                                                                '').replace(
        ',', '\n')
    today_min = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
    today_max = datetime.datetime.combine(datetime.date.today(), datetime.time.max)
    messages = str(len(Message.objects.filter(datetime__range=(today_min, today_max))))
    forward_lk = GeneralSettings.objects.get(id=1).forward_lk
    if forward_lk:
        send_lk = '✅'
    else:
        send_lk = '❌'
    auto_ans = GeneralSettings.objects.get(id=1).general_auto_answering
    if auto_ans:
        auto_ans = '✅'
    else:
        auto_ans = '❌'
    gen_delay = GeneralSettings.objects.get(id=1).general_delay
    gen_text = GeneralSettings.objects.get(id=1).general_text
    start_admin = MSG.start_admin.format(str(len(accounts)), messages, str(len(chats)), str(len(admins)), send_lk,
                                         forward_lk, auto_ans, gen_delay, gen_text)

    if call.message.chat.type == 'private':
        if 'do_nothing' in call.data.split(':'):
            pass
        else:

            bot.delete_message(call.message.chat.id, call.message.id)
            #  ok
            if 'start:admin' in call.data:
                bot.send_message(chat_id=call.message.chat.id, text=start_admin,
                                 reply_markup=KB.admin_menu_markup(is_spam_active))
            elif 'menu' in call.data:
                if 'mailing' in call.data.split(':'):
                    if 'starting' in call.data.split(':'):
                        if 'accounts' in call.data.split(':'):
                            bot.send_message(chat_id=call.message.chat.id, text=MSG.get_accounts,
                                             reply_markup=KB.get_accounts_markup(accounts, selected_accounts))
                        elif 'add_chats' in call.data.split(':'):
                            def add_chats(message):
                                chats = str(message.text).split('\n')
                                for chat in chats:
                                    try:
                                        if 'https://t.me/' in chat:
                                            try:
                                                chat_data = hd.get_chat_info(chat)
                                                title = chat_data[0]
                                                sub = chat_data[1]
                                                sleep(0.3)
                                                if not title and not sub:
                                                    Chat.objects.create(username=chat, subscribers=sub, title=title,
                                                                        is_active=False)
                                                else:
                                                    Chat.objects.create(username=chat, subscribers=sub, title=title,
                                                                        is_active=False)
                                                bot.send_message(message.chat.id, text=MSG.add_chats_success.format(chat))
                                            except:
                                                print(traceback.format_exc())
                                                title = ''
                                                sub = 0
                                                sleep(0.3)
                                                Chat.objects.create(username=chat, subscribers=sub, title=title, is_active=False)
                                                bot.send_message(message.chat.id, text=MSG.add_chats_success.format(chat))
                                        else:
                                            bot.send_message(message.chat.id, text=MSG.add_chats_fail.format(chat))
                                    except:
                                        if 'UNIQUE constraint failed' in traceback.format_exc():
                                            bot.send_message(message.chat.id, text=f'🛑 Чат {chat} уже в базе ...')
                                bot.send_message(message.chat.id, text=start_admin,
                                                 reply_markup=KB.admin_menu_markup(spam=is_spam_active))

                            msg = bot.send_message(call.message.chat.id, text=MSG.add_chats, reply_markup=KB.del_msg())
                            bot.register_next_step_handler(msg, add_chats)
                        elif 'lk' in call.data.split(':'):
                            bot.send_message(chat_id=call.message.chat.id, text=MSG.get_accounts,
                                             reply_markup=KB.get_accounts_for_lk_markup(accounts,
                                                                                        selected_accounts_for_lk))
                    elif 'start_lk' in call.data.split(':'):
                        #  Старт спама по ЛС. Заносим в БД is_spam_lk_active=True
                        if selected_accounts_for_lk:
                            print(selected_accounts_for_lk)
                            for acc in selected_accounts_for_lk:
                                print(acc)
                                Account.objects.filter(id_account=acc).update(is_spam_lk_active=True)
                            bot.send_message(chat_id=call.message.chat.id, text=MSG.spam_lk_started)
                            bot.send_message(chat_id=call.message.chat.id, text=start_admin,
                                             reply_markup=KB.admin_menu_markup(is_spam_active))
                        else:
                            bot.send_message(chat_id=call.message.chat.id, text=MSG.spam_accounts_not_selected,
                                             reply_markup=KB.admin_menu_markup(is_spam_active))
                    elif 'select_account' in call.data.split(':'):
                        selected_accounts.append(call.data.split(':')[-1])
                        bot.send_message(chat_id=call.message.chat.id, text=MSG.get_accounts,
                                         reply_markup=KB.get_accounts_markup(accounts, selected_accounts))
                    elif 'select_account_for_lk' in call.data.split(':'):
                        selected_accounts_for_lk.append(call.data.split(':')[-1])
                        bot.send_message(chat_id=call.message.chat.id, text=MSG.get_accounts_for_lk,
                                         reply_markup=KB.get_accounts_for_lk_markup(accounts, selected_accounts_for_lk))
                    elif 'start' in call.data.split(':'):
                        #  Старт спама по Группам. Заносим в БД is_spam_active=True
                        if selected_accounts:
                            for acc_id in selected_accounts:
                                Account.objects.filter(id_account=acc_id).update(is_spam_active=True)
                            bot.send_message(chat_id=call.message.chat.id, text=MSG.spam_started)
                            bot.send_message(chat_id=call.message.chat.id, text=start_admin,
                                             reply_markup=KB.admin_menu_markup(is_spam_active))
                        else:
                            bot.send_message(chat_id=call.message.chat.id, text=MSG.spam_accounts_not_selected,
                                             reply_markup=KB.admin_menu_markup(is_spam_active))
                        try:
                            os.system('systemctl restart post_to_chats.service')
                        except:
                            print(traceback.format_exc())
                    elif 'stop' in call.data.split(':'):
                        #  Старт спама по Группам. Заносим в БД is_spam_active=False
                        Account.objects.all().update(is_spam_active=False)
                        bot.send_message(chat_id=call.message.chat.id, text=MSG.spam_stopped)
                        bot.send_message(chat_id=call.message.chat.id, text=start_admin,
                                         reply_markup=KB.admin_menu_markup(is_spam_active))
                        try:
                            os.system('systemctl restart post_to_chats.service')
                        except:
                            print(traceback.format_exc())
                elif 'account' in call.data.split(':'):
                    if 'account_panel' in call.data.split(':'):
                        bot.send_message(chat_id=call.message.chat.id, text=start_admin,
                                         reply_markup=KB.accounts_panel())
                    elif 'add' in call.data.split(':'):
                        def add_account_id(message):
                            try:
                                id_acc = int(message.text)
                                Account.objects.create(id_account=id_acc)

                                def add_account_username(message):
                                    username = message.text
                                    if 'https://t.me/' in username:
                                        Account.objects.filter(id_account=id_acc).update(username=username)

                                        def add_account_api_hash_id(message):
                                            try:
                                                api_id = int(str(message.text).split(':')[0].strip())
                                                api_hash = message.text.split(':')[1].strip()
                                                Account.objects.filter(id_account=id_acc).update(api_id=api_id,
                                                                                                 api_hash=api_hash)

                                                def add_account_phone(message):
                                                    phone = str(message.text).replace(' ', '').strip()
                                                    if '+' in phone:
                                                        Account.objects.filter(id_account=id_acc).update(phone=phone)

                                                        with open('flag.txt', 'w') as file:
                                                            file.write(f'1:{id_acc}')

                                                        def add_account_code(message):
                                                            acc = Account.objects.filter(id_account=id_acc)[0]
                                                            acc_id = str(acc.id_account)
                                                            username = acc.username
                                                            api_id = str(acc.api_id)
                                                            api_hash = acc.api_hash
                                                            phone = acc.phone
                                                            code = message.text
                                                            Account.objects.filter(id_account=id_acc).update(
                                                                sms_code=code, is_auto_answering_active=True)

                                                            bot.send_message(call.message.chat.id,
                                                                             text=MSG.add_account_success.format(
                                                                                 acc_id, username, api_id, api_hash,
                                                                                 phone),
                                                                             reply_markup=KB.accounts_panel())

                                                        msg = bot.send_message(call.message.chat.id,
                                                                               text=MSG.add_account_code,
                                                                               reply_markup=KB.del_msg(id_acc))
                                                        bot.register_next_step_handler(msg, add_account_code)
                                                    else:
                                                        Account.objects.filter(id_account=id_acc).delete()
                                                        bot.send_message(message.chat.id,
                                                                         text=MSG.add_account_phone_fail,
                                                                         reply_markup=KB.accounts_panel())

                                                msg = bot.send_message(call.message.chat.id, text=MSG.add_account_phone,
                                                                       reply_markup=KB.del_msg(id_acc))
                                                bot.register_next_step_handler(msg, add_account_phone)
                                            except:
                                                print(traceback.format_exc())
                                                Account.objects.filter(id_account=id_acc).delete()
                                                bot.send_message(message.chat.id, text=MSG.add_account_api_hash_id_fail,
                                                                 reply_markup=KB.accounts_panel())

                                        msg = bot.send_message(call.message.chat.id, text=MSG.add_account_api_hash_id,
                                                               reply_markup=KB.del_msg(id_acc))
                                        bot.register_next_step_handler(msg, add_account_api_hash_id)
                                    else:
                                        Account.objects.filter(id_account=id_acc).delete()
                                        bot.send_message(message.chat.id, text=MSG.add_account_username_fail,
                                                         reply_markup=KB.accounts_panel())

                                msg = bot.send_message(call.message.chat.id, text=MSG.add_account_username,
                                                       reply_markup=KB.del_msg(id_acc))
                                bot.register_next_step_handler(msg, add_account_username)
                            except:
                                print(traceback.format_exc())
                                bot.send_message(message.chat.id, text=MSG.add_account_id_fail,
                                                 reply_markup=KB.accounts_panel())
                            # bot.send_message(message.chat.id, text=start_admin, reply_markup=KB.admin_menu_markup(spam=is_spam_active))

                        msg = bot.send_message(call.message.chat.id, text=MSG.add_account_id, reply_markup=KB.del_msg())
                        bot.register_next_step_handler(msg, add_account_id)
                    elif 'search' in call.data.split(':'):
                        bot.send_message(call.message.chat.id, text=MSG.get_all_accounts,
                                         reply_markup=KB.get_all_accounts_markup(accounts))
                    elif 'edit' in call.data.split(':'):
                        acc_id = call.data.split(':')[-1]
                        acc = Account.objects.get(id_account=acc_id)
                        delay = acc.delay
                        common_text = acc.common_text
                        auto_answering_text = acc.auto_answering_text
                        is_auto_answering_active = acc.is_auto_answering_active
                        bot.send_message(call.message.chat.id,
                                         text=MSG.get_account_details.format(f"{common_text if common_text else '❌'}",
                                                                             f"{auto_answering_text if auto_answering_text else '❌'}",
                                                                             f"{'✅' if is_auto_answering_active else '❌'}",
                                                                             f"{delay if delay else 0}"),
                                         reply_markup=KB.get_account_details(acc_id,
                                                                             is_auto_answering=is_auto_answering_active))
                    elif 'del_acc' in call.data.split(':'):
                        id_acc = call.data.split(':')[-1]
                        Account.objects.get(id_account=id_acc).delete()
                        accounts = [(account.id_account, account.username) for account in Account.objects.all()]
                        bot.send_message(call.message.chat.id, text=MSG.account_delete_success.format(str(id_acc)),
                                         reply_markup=KB.get_all_accounts_markup(accounts))
                    elif 'check_all' in call.data.split(':'):
                        bot.send_message(call.message.chat.id, text=MSG.checking_accounts)
                        with open('flag2.txt', 'w') as file:
                            flag = file.write(str(call.message.chat.id))
                        bot.send_message(call.message.chat.id, text=MSG.start_admin, reply_markup=KB.accounts_panel())
                    elif 'set_common_text' in call.data.split(':'):
                        acc_id = call.data.split(':')[-1]
                        acc = Account.objects.get(id_account=acc_id)
                        delay = acc.delay
                        auto_answering_text = acc.auto_answering_text
                        is_auto_answering_active = acc.is_auto_answering_active

                        def set_common_text(message):
                            common_text = message.text
                            Account.objects.filter(id_account=acc_id).update(common_text=common_text)
                            bot.send_message(call.message.chat.id, text=MSG.set_common_text_success.format(common_text))
                            bot.send_message(call.message.chat.id,
                                             text=MSG.get_account_details.format(
                                                 f"{common_text if common_text else '❌'}",
                                                 f"{auto_answering_text if auto_answering_text else '❌'}",
                                                 f"{'✅' if is_auto_answering_active else '❌'}",
                                                 f"{delay if delay else 0}"),
                                             reply_markup=KB.get_account_details(acc_id,
                                                                                 is_auto_answering=is_auto_answering_active))

                        msg = bot.send_message(call.message.chat.id, text=MSG.set_common_text,
                                               reply_markup=KB.del_msg())
                        bot.register_next_step_handler(msg, set_common_text)
                    elif 'set_auto_text' in call.data.split(':'):
                        acc_id = call.data.split(':')[-1]
                        acc = Account.objects.get(id_account=acc_id)
                        delay = acc.delay
                        common_text = acc.common_text
                        auto_answering_text = acc.auto_answering_text
                        is_auto_answering_active = acc.is_auto_answering_active

                        def set_auto_text(message):
                            auto_text = message.text
                            Account.objects.filter(id_account=acc_id).update(auto_answering_text=auto_text)
                            bot.send_message(call.message.chat.id, text=MSG.set_auto_text_success.format(auto_text))
                            bot.send_message(call.message.chat.id,
                                             text=MSG.get_account_details.format(
                                                 f"{common_text if common_text else '❌'}",
                                                 f"{auto_text if auto_text else '❌'}",
                                                 f"{'✅' if is_auto_answering_active else '❌'}",
                                                 f"{delay if delay else 0}"),
                                             reply_markup=KB.get_account_details(acc_id,
                                                                                 is_auto_answering=is_auto_answering_active))

                        msg = bot.send_message(call.message.chat.id, text=MSG.set_auto_text, reply_markup=KB.del_msg())
                        bot.register_next_step_handler(msg, set_auto_text)
                    elif 'set_auto_answer' in call.data.split(':'):
                        acc_id = call.data.split(':')[-1]
                        is_auto_answer = Account.objects.get(id_account=acc_id).is_auto_answering_active

                        if is_auto_answer:
                            Account.objects.filter(id_account=acc_id).update(is_auto_answering_active=False)
                            acc = Account.objects.get(id_account=acc_id)
                            delay = acc.delay
                            common_text = acc.common_text
                            auto_answering_text = acc.auto_answering_text
                            is_auto_answering_active = acc.is_auto_answering_active
                            bot.send_message(call.message.chat.id,
                                             text=MSG.get_account_details.format(
                                                 f"{common_text if common_text else '❌'}",
                                                 f"{auto_answering_text if auto_answering_text else '❌'}",
                                                 f"{'✅' if is_auto_answering_active else '❌'}",
                                                 f"{delay if delay else 0}"),
                                             reply_markup=KB.get_account_details(acc_id,
                                                                                 is_auto_answering=is_auto_answering_active))
                        else:
                            Account.objects.filter(id_account=acc_id).update(is_auto_answering_active=True)
                            acc = Account.objects.get(id_account=acc_id)
                            delay = acc.delay
                            common_text = acc.common_text
                            auto_answering_text = acc.auto_answering_text
                            is_auto_answering_active = acc.is_auto_answering_active
                            bot.send_message(call.message.chat.id,
                                             text=MSG.get_account_details.format(
                                                 f"{common_text if common_text else '❌'}",
                                                 f"{auto_answering_text if auto_answering_text else '❌'}",
                                                 f"{'✅' if is_auto_answering_active else '❌'}",
                                                 f"{delay if delay else 0}"),
                                             reply_markup=KB.get_account_details(acc_id,
                                                                                 is_auto_answering=is_auto_answering_active))
                    elif 'set_timeout' in call.data.split(':'):
                        acc_id = call.data.split(':')[-1]
                        acc = Account.objects.get(id_account=acc_id)
                        is_auto_answering_active = acc.is_auto_answering_active
                        delay = acc.delay
                        common_text = acc.common_text
                        auto_answering_text = acc.auto_answering_text

                        def set_timeout(message):
                            try:
                                timeout = int(message.text)
                                Account.objects.filter(id_account=acc_id).update(delay=timeout)
                                bot.send_message(call.message.chat.id, text=MSG.set_timeout_success.format(timeout))
                                bot.send_message(call.message.chat.id,
                                                 text=MSG.get_account_details.format(
                                                     f"{common_text if common_text else '❌'}",
                                                     f"{auto_answering_text if auto_answering_text else '❌'}",
                                                     f"{'✅' if is_auto_answering_active else '❌'}",
                                                     f"{timeout if timeout else 0}"),
                                                 reply_markup=KB.get_account_details(acc_id,
                                                                                     is_auto_answering=is_auto_answering_active))
                            except:
                                bot.send_message(call.message.chat.id, text=MSG.set_timeout_fail.format(message.text))
                                bot.send_message(call.message.chat.id,
                                                 text=MSG.get_account_details.format(
                                                     f"{common_text if common_text else '❌'}",
                                                     f"{auto_answering_text if auto_answering_text else '❌'}",
                                                     f"{'✅' if is_auto_answering_active else '❌'}",
                                                     f"{delay if delay else 0}"),
                                                 reply_markup=KB.get_account_details(acc_id,
                                                                                     is_auto_answering=is_auto_answering_active))

                        msg = bot.send_message(call.message.chat.id, text=MSG.set_timeout, reply_markup=KB.del_msg())
                        bot.register_next_step_handler(msg, set_timeout)
                    elif 'set_default' in call.data.split(':'):
                        acc_id = call.data.split(':')[-1]
                        Account.objects.filter(id_account=acc_id).update(common_text='', auto_answering_text='',
                                                                         is_auto_answering_active=False, delay=0)
                        acc = Account.objects.get(id_account=acc_id)
                        is_auto_answering_active = acc.is_auto_answering_active
                        delay = acc.delay
                        common_text = acc.common_text
                        auto_answering_text = acc.auto_answering_text
                        bot.send_message(call.message.chat.id,
                                         text=MSG.get_account_details.format(
                                             f"{common_text if common_text else '❌'}",
                                             f"{auto_answering_text if auto_answering_text else '❌'}",
                                             f"{'✅' if is_auto_answering_active else '❌'}",
                                             f"{delay if delay else 0}"),
                                         reply_markup=KB.get_account_details(acc_id,
                                                                             is_auto_answering=is_auto_answering_active))
                elif 'chat' in call.data.split(':'):
                    if len(chats) > 25:
                        chats = chats[:25]
                        bot.send_message(call.message.chat.id, text=MSG.too_many_chats.format(web_admin_panel),
                                         reply_markup=KB.get_chats_markup(chats=chats))
                    else:
                        bot.send_message(call.message.chat.id, text=MSG.get_all_chats,
                                         reply_markup=KB.get_chats_markup(chats=chats))
                    if 'chat_details' in call.data.split(':'):
                        chat_id = call.data.split(':')[-1]
                        chat = Chat.objects.get(id=chat_id)
                        username = chat.username
                        chat_text = chat.text
                        delay = chat.delay
                        bot.send_message(call.message.chat.id,
                                         text=MSG.get_chat_details.format(username, chat_text, delay),
                                         reply_markup=KB.get_chat_details_markup(chat_id))
                    elif 'change_chat_text' in call.data.split(':'):
                        chat_id = call.data.split(':')[-1]

                        def change_chat_text(message):
                            text = message.text
                            Chat.objects.filter(id=chat_id).update(text=text)
                            chat = Chat.objects.get(id=chat_id)
                            username = chat.username
                            chat_text = chat.text
                            delay = chat.delay
                            bot.send_message(call.message.chat.id,
                                             text=MSG.get_chat_details.format(username, chat_text, delay),
                                             reply_markup=KB.get_chat_details_markup(chat_id))

                        msg = bot.send_message(call.message.chat.id, text=MSG.set_chat_text, reply_markup=KB.del_msg())
                        bot.register_next_step_handler(msg, change_chat_text)
                    elif 'set_chat_timeout' in call.data.split(':'):
                        chat_id = call.data.split(':')[-1]

                        def set_chat_timeout(message):
                            try:
                                _delay = int(message.text)
                                Chat.objects.filter(id=chat_id).update(delay=_delay)
                                chat = Chat.objects.get(id=chat_id)
                                username = chat.username
                                chat_text = chat.text
                                delay = chat.delay
                                bot.send_message(call.message.chat.id,
                                                 text=MSG.get_chat_details.format(username, chat_text, delay),
                                                 reply_markup=KB.get_chat_details_markup(chat_id))
                            except:
                                chat = Chat.objects.get(id=chat_id)
                                username = chat.username
                                chat_text = chat.text
                                delay = chat.delay
                                bot.send_message(call.message.chat.id, text=MSG.set_chat_timeout_fail)
                                bot.send_message(call.message.chat.id,
                                                 text=MSG.get_chat_details.format(username, chat_text, delay),
                                                 reply_markup=KB.get_chat_details_markup(chat_id))

                        msg = bot.send_message(call.message.chat.id, text=MSG.set_chat_timeout,
                                               reply_markup=KB.del_msg())
                        bot.register_next_step_handler(msg, set_chat_timeout)
                    elif 'del_chat' in call.data.split(':'):
                        chat_id = call.data.split(':')[-1]
                        username = Chat.objects.get(id=chat_id).username
                        Chat.objects.get(id=chat_id).delete()
                        chats = [(chat.username, chat.id) for chat in Chat.objects.all()]
                        bot.send_message(call.message.chat.id, text=MSG.chat_delete_success.format(username),
                                         reply_markup=KB.get_chats_markup(chats))
                elif 'settings' in call.data.split(':'):
                    if 'info' in call.data.split(':'):
                        settings = GeneralSettings.objects.get(id=1)
                        text = settings.general_text
                        auto = settings.general_auto_answering
                        delay = settings.general_delay
                        bot.send_message(call.message.chat.id,
                                         text=MSG.get_admins.format(admins_str, text, auto, delay),
                                         reply_markup=KB.settings_panel())
                    elif 'add_admin' in call.data.split(':'):
                        def add_admin(message):
                            try:
                                admin_id = int(str(message.text).split(':')[0])
                                admin_username = str(message.text).split('https://t.me/')[1]
                                TGAdmin.objects.create(user_id=admin_id, username='@' + admin_username)
                                bot.send_message(call.message.chat.id,
                                                 text=MSG.add_admin_success.format(admin_username),
                                                 reply_markup=KB.settings_panel())
                            except:
                                print(traceback.format_exc())
                                bot.send_message(call.message.chat.id, text=MSG.add_admin_fail,
                                                 reply_markup=KB.settings_panel())

                        msg = bot.send_message(call.message.chat.id, text=MSG.add_admin, reply_markup=KB.del_msg())
                        bot.register_next_step_handler(msg, add_admin)
                    elif 'del_admin' in call.data.split(':'):
                        admins = [(admin.username, admin.user_id) for admin in TGAdmin.objects.all()]
                        bot.send_message(call.message.chat.id, text=MSG.get_admin_details,
                                         reply_markup=KB.get_admins_markup(admins))
                    elif 'delete_admin' in call.data.split(':'):
                        admin_id = call.data.split(':')[-1]
                        TGAdmin.objects.get(user_id=admin_id).delete()
                        admins = [(admin.username, admin.user_id) for admin in TGAdmin.objects.all()]
                        bot.send_message(call.message.chat.id, text=MSG.admin_delete_success,
                                         reply_markup=KB.get_admins_markup(admins))
                    elif 'set_auto_answering' in call.data.split(':'):
                        def set_general_auto_answer(message):
                            text = message.text
                            GeneralSettings.objects.filter(id=1).update(general_auto_answering=text)
                            bot.send_message(call.message.chat.id, text=MSG.set_general_auto_answer_success)
                            settings = GeneralSettings.objects.get(id=1)
                            text = settings.general_text
                            auto = settings.general_auto_answering
                            delay = settings.general_delay
                            bot.send_message(call.message.chat.id,
                                             text=MSG.get_admins.format(admins_str, text, auto, delay),
                                             reply_markup=KB.settings_panel())

                        msg = bot.send_message(call.message.chat.id, text=MSG.set_general_auto_answer,
                                               reply_markup=KB.del_msg())
                        bot.register_next_step_handler(msg, set_general_auto_answer)
                    elif 'set_timeout' in call.data.split(':'):
                        def set_timeout(message):
                            try:
                                timeout = int(message.text)
                                GeneralSettings.objects.filter(id=1).update(general_delay=timeout)
                                bot.send_message(call.message.chat.id,
                                                 text=MSG.set_general_timeout_success.format(timeout))
                                settings = GeneralSettings.objects.get(id=1)
                                text = settings.general_text
                                auto = settings.general_auto_answering
                                delay = settings.general_delay
                                bot.send_message(call.message.chat.id,
                                                 text=MSG.get_admins.format(admins_str, text, auto, delay),
                                                 reply_markup=KB.settings_panel())
                            except:
                                bot.send_message(call.message.chat.id,
                                                 text=MSG.set_chat_timeout_fail.format(message.text))
                                settings = GeneralSettings.objects.get(id=1)
                                text = settings.general_text
                                auto = settings.general_auto_answering
                                delay = settings.general_delay
                                bot.send_message(call.message.chat.id,
                                                 text=MSG.get_admins.format(admins_str, text, auto, delay),
                                                 reply_markup=KB.settings_panel())

                        msg = bot.send_message(call.message.chat.id, text=MSG.set_general_timeout,
                                               reply_markup=KB.del_msg())
                        bot.register_next_step_handler(msg, set_timeout)
                    elif 'set_general_text' in call.data.split(':'):
                        def set_general_text(message):
                            text = message.text
                            GeneralSettings.objects.filter(id=1).update(general_text=text)
                            bot.send_message(call.message.chat.id, text=MSG.set_general_text_success)
                            settings = GeneralSettings.objects.get(id=1)
                            text = settings.general_text
                            auto = settings.general_auto_answering
                            delay = settings.general_delay
                            bot.send_message(call.message.chat.id,
                                             text=MSG.get_admins.format(admins_str, text, auto, delay),
                                             reply_markup=KB.settings_panel())

                        msg = bot.send_message(call.message.chat.id, text=MSG.set_general_text,
                                               reply_markup=KB.del_msg())
                        bot.register_next_step_handler(msg, set_general_text)
            elif 'back' in call.data.split(':'):
                id_acc = call.data.split(':')[-1]
                selected_accounts.clear()
                selected_accounts_for_lk.clear()
                try:
                    Account.objects.filter(id_account=id_acc).delete()
                except:
                    pass
                bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
                bot.send_message(chat_id=call.message.chat.id, text=start_admin,
                                 reply_markup=KB.admin_menu_markup(is_spam_active))

            elif 'help' in call.data.split(':'):
                bot.send_message(call.message.chat.id, text=MSG.get_help, reply_markup=KB.del_msg())
            elif 'refresh' in call.data:
                bot.send_message(chat_id=call.message.chat.id, text=start_admin,
                                 reply_markup=KB.admin_menu_markup(is_spam_active))


bot.infinity_polling()
