from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin

from users.models import FoodgramUser


@register(FoodgramUser)
class FoodgramUserAdmin(UserAdmin):
    empty_value_display = 'Не задано'
    list_display = ("username", "email", "first_name", "last_name")
    search_fields = (
        "username",
        "email",
    )
    list_filter = (
        "username",
        "email",
    )
