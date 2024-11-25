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
