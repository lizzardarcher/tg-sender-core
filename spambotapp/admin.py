from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.utils.html import format_html

from spambotapp.models import Account, Chat, Client, MasterAccount, GeneralLogging, AccountLogging, Bot, TGAdmin, \
    GeneralSettings, Message

admin.site.site_url = ''
admin.site.site_header = "Telegram-Bot Админ Панель"
admin.site.site_title = "Telegram-Bot"
admin.site.index_title = "Добро пожаловать в Telegram-Bot Админ Панель"


class GeneralSettingsAdmin(admin.ModelAdmin):

    def get_actions(self, request):
        actions = super().get_actions(request)
        if request.user.username[0].upper() != "J":
            if "delete_selected" in actions:
                del actions["delete_selected"]
        return actions


class AccountAdmin(admin.ModelAdmin):
    list_display = ('datetime', 'username', 'phone', 'status', 'is_spam_active', 'delay')
    list_display_links = ('datetime', 'username', 'phone', 'status', 'is_spam_active', 'delay')
    search_fields = ('username',)


class MessageAdmin(admin.ModelAdmin):
    list_display = ('datetime', 'message_id', 'account', 'chat', 'is_deleted')
    list_display_links = ('datetime', 'message_id', 'account', 'chat', 'is_deleted')


class ChatAdmin(admin.ModelAdmin):
    list_display = ('datetime', 'title', 'username', 'delay')
    list_display_links = ('datetime', 'title', 'username', 'delay')


class ClientAdmin(admin.ModelAdmin):
    list_display = ('datetime', 'username', 'first_name', 'last_name', 'phone', 'next_time_contact', 'exchange_time',
                    'exchange_value', 'is_spam_active')
    list_display_links = ('datetime', 'username', 'first_name', 'last_name', 'phone', 'next_time_contact',
                          'exchange_time', 'exchange_value', 'is_spam_active')


class MasterAccountAdmin(admin.ModelAdmin):
    list_display = ('username', 'status', 'is_master', 'is_duplicate')
    list_display_links = ('username', 'status', 'is_master', 'is_duplicate')


class GeneralLoggingAdmin(admin.ModelAdmin):
    def get_log_level(self, obj):
        if obj.log_level == 'Info':
            return format_html('<div style="color:aqua;">%s</div>' % obj.log_level)
        elif obj.log_level == 'Fatal':
            return format_html('<div style="color:red;">%s</div>' % obj.log_level)
        elif obj.log_level == 'Warning':
            return format_html('<div style="color:orange;">%s</div>' % obj.log_level)
        # elif obj.log_level == 'Trace':
        #     return format_html('<div style="color:white;">%s</div>' % obj.log_level)
        # elif obj.log_level == 'Debug':
        #     return format_html('<div style="color:white;">%s</div>' % obj.log_level)
        return obj.log_level

    get_log_level.allow_tags = True
    get_log_level.short_description = 'log_level'
    list_display = ('datetime', 'get_log_level', 'message', 'account', 'chat')
    list_display_links = ('get_log_level', 'message', 'account', 'chat')


class AccountLoggingAdmin(admin.ModelAdmin):
    def get_log_level(self, obj):
        if obj.log_level == 'Info':
            return format_html('<div style="color:aqua;">%s</div>' % obj.log_level)
        elif obj.log_level == 'Fatal':
            return format_html('<div style="color:red;">%s</div>' % obj.log_level)
        elif obj.log_level == 'Warning':
            return format_html('<div style="color:orange;">%s</div>' % obj.log_level)
        # elif obj.log_level == 'Trace':
        #     return format_html('<div style="color:white;">%s</div>' % obj.log_level)
        # elif obj.log_level == 'Debug':
        #     return format_html('<div style="color:white;">%s</div>' % obj.log_level)
        return obj.log_level

    get_log_level.allow_tags = True
    get_log_level.short_description = 'log_level'
    list_display = ('datetime', 'get_log_level', 'message', 'account', 'chat')
    list_display_links = ('get_log_level', 'message', 'account', 'chat')


class BotAdmin(admin.ModelAdmin):
    list_display = ('link', 'token')
    list_display_links = ('link', 'token')


class TGAdminAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username')
    list_display_links = ('user_id', 'username')


admin.site.register(Account, AccountAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Chat, ChatAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(MasterAccount, MasterAccountAdmin)
admin.site.register(GeneralLogging, GeneralLoggingAdmin)
admin.site.register(AccountLogging, AccountLoggingAdmin)
admin.site.register(Bot, BotAdmin)
admin.site.register(TGAdmin, TGAdminAdmin)
admin.site.register(GeneralSettings, GeneralSettingsAdmin)

# admin.site.unregister(User)
admin.site.unregister(Group)
