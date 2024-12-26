from django.core.validators import RegexValidator


class UserValidators:
    """Класс валидаторов для пользователей Foodgram."""

    username_validator = RegexValidator(
        regex=r"^[\w.@+-]+\Z",
        message="Username: некорректное имя",
        code="invalid_username",
    )


class RecipeValidators:
    """Класс валидаторов для рецептов Foodgram."""

    slug_validator = RegexValidator(
        regex=r"^[-a-zA-Z0-9_]+$",
        message="Некорректный слаг",
        code="invalid_slug",
    )
