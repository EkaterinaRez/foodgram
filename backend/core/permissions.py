from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """Разрешение позволяет только администраторам изменять объект.

    Все остальные пользователи могут только читать.

    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and (
            request.user.role == 'admin' or request.user.is_superuser
        )
