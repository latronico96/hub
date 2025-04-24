"""
Admin module for managing Unidad, Producto and Receta models in the Django admin
 interface.
"""

from django.contrib import admin

from recetario.models import Producto, Receta, Unidad

admin.site.register(Unidad)
admin.site.register(Producto)
admin.site.register(Receta)
