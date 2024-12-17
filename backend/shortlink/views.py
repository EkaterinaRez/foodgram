from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from .models import UrlShort


def redirect_to_long_url(request, short_url):
    """Переадресация на полный адрес с короткого."""

    try:
        url_short = get_object_or_404(UrlShort, short_url=short_url)
        return redirect(url_short.long_url)
    except UrlShort.DoesNotExist:
        return HttpResponse("Link not found.", status=404)
