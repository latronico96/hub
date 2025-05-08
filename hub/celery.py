from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from hub.settings import is_testing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hub.settings")

app = Celery("hub")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

print(f"[SETTINGS] ENV is_testing: {is_testing}")