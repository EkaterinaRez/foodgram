from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.db import models

from core.validators import UserValidators


class FoodgramUser(AbstractUser):
    """Модель пользователя Foodgram."""

    username = models.CharField(
        "Имя пользователя",
        max_length=150,
        unique=True,
        validators=[UserValidators.username_validator],
        help_text="Уникальное имя пользователя без спец.символов и пробелов.",
    )
    email = models.EmailField(
        "Почта",
        max_length=254,
        unique=True,
        validators=[UserValidators.email_validator],
    )
    first_name = models.CharField(
        "Имя",
        max_length=150,
        validators=[UserValidators.fio_validator],
    )
    last_name = models.CharField(
        "Фамилия",
        max_length=150,
        validators=[UserValidators.fio_validator],
    )
    password = models.CharField(
        "Пароль",
        max_length=128,
        help_text="Пароль должен быть надежным.",
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"Имя пользователя: {self.username}"

    def save(self, *args, **kwargs):
        self.password = make_password(self.password)
        super().save(*args, **kwargs)


class Subscription(models.Model):
    """Модель подписки на авторов."""

    user = models.ForeignKey(
        FoodgramUser,
        verbose_name="Подписчик",
        related_name="subscriptions",
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        FoodgramUser,
        verbose_name="Автор рецептов",
        on_delete=models.CASCADE,
        related_name="subscribers",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = (
            models.UniqueConstraint(
                fields=("user", "author"),
                name="unique_subscription",
            ),
            models.CheckConstraint(
                check=~models.Q(author=models.F("user")),
                name="subs_to_self",
            ),
        )

    def __str__(self):
        return f"Подписка: {self.user} подписался на: {self.author}"
