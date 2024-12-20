from django.db import models


class UrlShort(models.Model):
    """Модель для создания коротких ссылок."""

    long_url = models.URLField(unique=True)
    short_url = models.URLField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ссылка'
        verbose_name_plural = 'Ссылки'

    def __str__(self):
        return self.short_url
