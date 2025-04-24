"""
Este archivo configura la administración de modelos para la aplicación 'users'.
"""

from django.contrib import admin

from users.models import User

admin.site.register(User)
