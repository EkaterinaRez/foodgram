from django.contrib import admin

from .models import (UrlShort)


@admin.register(UrlShort)
class SubscriptionAdmin(admin.ModelAdmin):
    empty_value_display = 'Не задано'
    list_display = ("long_url", "short_url", "created_at")
    search_fields = ("long_url", "short_url")
    list_filter = ("long_url", "short_url")
    ordering = ("-created_at",)
