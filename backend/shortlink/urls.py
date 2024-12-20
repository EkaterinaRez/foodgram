from django.urls import path

from . import views


urlpatterns = [
    path('', views.redirect_to_long_url,
         name='redirect_to_long_url'),
]
