from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import User, Subscription


@admin.register(User)
class UserAdmin(UserAdmin):
    empty_value_display = 'Не задано'
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    ordering = ('username',)
    readonly_fields = ('last_login', 'date_joined')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    empty_value_display = 'Не задано'
    list_display = ('user', 'author')
    list_filter = ('user__username', 'author__username')
    ordering = ('-id',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related(
            'user', 'author'
        )
        return queryset
