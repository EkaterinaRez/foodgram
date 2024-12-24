from django.shortcuts import get_object_or_404, redirect
from .models import UrlShort


def redirect_to_long_url(request, short_url):
    """Переадресация на полный адрес с короткого."""
    long_url = get_object_or_404(UrlShort, short_url=short_url).long_url
    return redirect(long_url)
