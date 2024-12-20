import string
from random import choice, randint

from core.constants import MAX_GEN, MIN_GEN


def generate_short_url():
    """Генерирует случайную последовательность."""

    # base_url = getattr(settings,
    #                    'DOMAIN_URL',
    #                    'http://localhost:8000'
    #                    )
    # randomize = ''.join(
    #     choice(string.ascii_letters + string.digits)
    #     for _ in range(randint(MIN_GEN, MAX_GEN)))

    # return f'{base_url}/s/{randomize}/'
    return ''.join(
        choice(string.ascii_letters + string.digits)
        for _ in range(randint(MIN_GEN, MAX_GEN)))
