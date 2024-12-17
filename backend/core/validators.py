from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


class UserValidators:
    """Класс валидаторов для пользователей Foodgram."""

    username_validator = RegexValidator(
        regex=r"^[\w.@+-]+\Z",
        message="Username: некорректное имя",
        code="invalid_username",
    )

    email_validator = RegexValidator(
        regex=r"[^@]+@[^@]+\.[^@]+",
        message="Email: некорректный адрес электронной почты",
        code="invalid_email",
    )

    fio_validator = RegexValidator(
        regex=r"^[A-ZА-ЯЁ][a-zа-яё]*(?:[- ][A-ZА-ЯЁ][a-zа-яё]*)*$",
        message="Некорректное ФИО",
        code="invalid_fio",
    )


class RecipeValidators:
    """Класс валидаторов для рецептов Foodgram."""

    slug_validator = RegexValidator(
        regex=r"^[-a-zA-Z0-9_]+$",
        message="Некорректный слаг",
        code="invalid_slug",
    )

    @staticmethod
    def cook_time_validator(value):
        if value <= 0:
            raise ValidationError(
                'Время приготовления должно быть больше нуля.'
            )

    @staticmethod
    def count_ingredients_validator(value):
        if value <= 0:
            raise ValidationError(
                'Количество ингредиентов должно быть больше нуля.'
            )
