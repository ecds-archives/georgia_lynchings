import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'georgia_lynchings.settings'

from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()


