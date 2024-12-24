import string
from random import choice, randint

from core.constants import MAX_GEN, MIN_GEN


def generate_short_url():
    """Генерирует случайную последовательность."""
    return ''.join(
        choice(string.ascii_letters + string.digits)
        for _ in range(randint(MIN_GEN, MAX_GEN)))
