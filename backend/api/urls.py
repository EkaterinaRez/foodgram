from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (UserViewSet, IngredientViewSet, RecipeViewSet,
                       TagViewSet, redirect_to_long_url)

api_router = DefaultRouter()
api_router.register('tags', TagViewSet, basename='tags')
api_router.register('ingredients', IngredientViewSet, basename='ingredients')
api_router.register(r'recipes', RecipeViewSet, basename='recipes')
api_router.register(r'users', UserViewSet, basename='users')


urlpatterns_detail = [
    path('s/<str:short_url>', redirect_to_long_url,
         name='redirect_to_long_url'),
    path('', include(api_router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]

urlpatterns = [
    path('', include(urlpatterns_detail)),
]
