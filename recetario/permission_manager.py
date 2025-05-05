from django.contrib.auth.models import Permission

from users.models import User


class PermissionManager:
    # pylint: disable=too-few-public-methods
    ADMIN_ROlE = "Admin"
    USER_ROLE = "User"
    VISIT_ROLE = "Visit"
    _ROLES_PERMISSIONS = {
        ADMIN_ROlE: [
            "view_unidad",
            "add_unidad",
            "change_unidad",
            "delete_unidad",
            "view_producto",
            "add_producto",
            "change_producto",
            "delete_producto",
            "view_receta",
            "add_receta",
            "change_receta",
            "delete_receta",
        ],
        USER_ROLE: [
            "view_unidad",
            "add_unidad",
            "change_unidad",
            "delete_unidad",
            "view_producto",
            "add_producto",
            "change_producto",
            "delete_producto",
            "view_receta",
            "add_receta",
            "change_receta",
            "delete_receta",
        ],
        VISIT_ROLE: [
            "view_unidad",
            "view_producto",
            "view_receta",
        ],
    }

    @classmethod
    def assign_permissions_to_user(cls, user: User, user_type_permissions: str) -> None:
        """Asigna un rol a un usuario, removiendo otros roles primero"""
        try:
            # Limpiar permisos existentes del usuario primero
            user.user_permissions.clear()

            for permission in cls._ROLES_PERMISSIONS[user_type_permissions]:
                # Obtener el permiso considerando el content_type
                app_label = "recetario"
                codename = permission
                permission_obj = Permission.objects.get(
                    content_type__app_label=app_label, codename=codename
                )
                user.user_permissions.add(permission_obj)
        except Permission.DoesNotExist as e:
            print(f"[!] Permiso no encontrado: {permission}")
            raise ValueError(f"El permiso '{permission}' no existe") from e
