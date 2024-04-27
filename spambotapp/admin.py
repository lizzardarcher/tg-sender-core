from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.utils.html import format_html

from spambotapp.models import *


admin.site.site_url = ''
admin.site.site_header = "Telegram-Bot Админ Панель"
admin.site.site_title = "Telegram-Bot"
admin.site.index_title = "Добро пожаловать в Telegram-Bot Админ Панель"

class ChannelToSubscribeAdmin(admin.ModelAdmin):
    list_display = ('username',)

class GeneralSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # def get_actions(self, request):
    #     actions = super().get_actions(request)
    #     if request.user.username[0].upper() != "J":
    #         if "delete_selected" in actions:
    #             del actions["delete_selected"]
    #     return actions
    fields = ('forward_lk', 'general_text', 'general_auto_answering', 'general_delay')

class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_enabled', 'datetime', 'username', 'phone', 'status', 'is_spam_active', 'delay', 'is_spam_lk_active')
    list_display_links = ('datetime', 'username', 'phone', 'status', 'is_spam_active', 'delay', 'is_spam_lk_active')
    search_fields = ('username',)


class MessageAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False
    list_display = ('datetime', 'message_id', 'account', 'chat', 'is_deleted')
    list_display_links = ('datetime', 'message_id', 'account', 'chat', 'is_deleted')

@admin.action(description="Пометить как отработанное")
def make_chat_worked_out(modeladmin, request, queryset):
    queryset.update(worked_out=True)

@admin.action(description="Пометить как неактивный")
def make_chat_inactive(modeladmin, request, queryset):
    queryset.update(is_active=False, worked_out=True)

class ChatAdmin(admin.ModelAdmin):

    def get_username(self, obj):
        return '@'+obj.username.split("/")[-1]

    def get_is_user_banned(self, obj):
        return "\n".join(['@'+p.username.split("/")[-1] for p in obj.is_user_banned.all()])

    get_username.admin_order_field = 'username'
    get_username.short_description = 'Username'
    get_is_user_banned.admin_order_field = 'is_user_banned'
    get_is_user_banned.short_description = 'Ban-list'

    filter_horizontal = ('is_user_banned',)

    search_fields = ('category', 'username', 'title', 'comment')
    list_display = ('category', 'title', 'username', 'subscribers', 'get_is_user_banned', 'is_emoji_allowed','is_del_mes_available',
                    'comment', 'delay', 'is_active', 'worked_out')
    list_display_links = ('title', 'username', 'delay', 'get_is_user_banned', 'is_emoji_allowed',
                    'comment', 'is_active')
    actions = [make_chat_worked_out, make_chat_inactive]
    list_per_page = 50

class ClientAdmin(admin.ModelAdmin):
    list_display = ('datetime', 'username', 'first_name', 'last_name', 'phone', 'next_time_contact', 'exchange_time',
                    'exchange_value', 'is_spam_active')
    list_display_links = ('datetime', 'username', 'first_name', 'last_name', 'phone', 'next_time_contact',
                          'exchange_time', 'exchange_value', 'is_spam_active')


class MasterAccountAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    list_display = ('username', 'status', 'is_master', 'is_duplicate')
    list_display_links = ('username', 'status', 'is_master', 'is_duplicate')


class GeneralLoggingAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False
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
    def has_add_permission(self, request, obj=None):
        return False
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
    list_display = ('datetime', 'get_log_level', 'message', 'account', 'chat', 'client')
    list_display_links = ('get_log_level', 'message', 'account', 'chat', 'client')

class BotAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    list_display = ('link', 'token')
    list_display_links = ('link', 'token')

class TGAdminAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username')
    list_display_links = ('user_id', 'username')


class ChatMasterAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False
    list_display = ('id', 'title', 'comment')
    list_display_links = ('id', 'title', 'comment')


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
admin.site.register(ChannelToSubscribe, ChannelToSubscribeAdmin)
admin.site.register(ChatMaster, ChatMasterAdmin)

# admin.site.unregister(User)
admin.site.unregister(Group)
