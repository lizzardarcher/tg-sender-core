import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()