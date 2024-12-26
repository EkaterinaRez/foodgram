from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (UserViewSet, IngredientViewSet, RecipeViewSet,
                       TagViewSet)

api_router = DefaultRouter()
api_router.register('tags', TagViewSet, basename='tags')
api_router.register('ingredients', IngredientViewSet, basename='ingredients')
api_router.register(r'recipes', RecipeViewSet, basename='recipes')
api_router.register(r'users', UserViewSet, basename='users')


urlpatterns_detail = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(api_router.urls)),
]

urlpatterns = [
    path('', include(urlpatterns_detail)),
]
