import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
django.setup()

from spambotapp.models import Account

spam_is_active = Account.objects.get(is_spam_active=True)

print(spam_is_active)
