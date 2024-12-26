from rest_framework import permissions


class IsAuthAuthorOrReadonly(permissions.BasePermission):
    """Разрешение позволяет только аторизованным авторам изменять объект."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user
