import string
from random import choice, randint

from django.db import models

from core.constants import MIN_GEN, MAX_GEN


def generate_short_url():
    """Генерирует случайную последовательность."""

    return ''.join(
        choice(string.ascii_letters + string.digits)
        for _ in range(randint(MIN_GEN, MAX_GEN))
    )


class UrlShort(models.Model):
    """Модель для создания коротких ссылок."""

    long_url = models.URLField(unique=True)
    short_url = models.CharField(
        max_length=MAX_GEN, default=generate_short_url, unique=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ссылка'
        verbose_name_plural = 'Ссылки'

    def __str__(self):
        return self.short_url
