from rest_framework import permissions, status
from rest_framework.response import Response


class IsAdminOrReadOnly(permissions.BasePermission):
    """Разрешение позволяет только администраторам изменять объект.

    Все остальные пользователи могут только читать.

    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_superuser


class IsAuthenticatedOr401(permissions.BasePermission):
    """Позволяет доступ только аутентифицированным пользователям."""

    def has_permission(self, request, view):
        is_authenticated = request.user and request.user.is_authenticated
        if not is_authenticated:
            Response(
                {"detail": "Аутентификация не выполнена."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return is_authenticated
