from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class ApiPagination(PageNumberPagination):
    """Пагинация для страниц API."""

    page_size_query_param = 'limit'
    page_size = settings.PAGE_SIZE
