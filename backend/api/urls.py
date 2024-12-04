from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (FoodgramUserViewSet,
                       IngredientViewSet,
                       TagViewSet,
                       RecipeViewSet,
                       SubscriptionViewSet)


api_router = DefaultRouter()
api_router.register('tags', TagViewSet, basename='tags')
api_router.register('ingredients', IngredientViewSet, basename='ingredients')
api_router.register(r'recipes', RecipeViewSet, basename='recipes')
api_router.register(r'users', FoodgramUserViewSet, basename='users')

users_subscriptions_view = SubscriptionViewSet.as_view(
    {'get': 'list_subscriptions'})
users_subscribe_view = SubscriptionViewSet.as_view({'post': 'subscribe'})


urlpatterns_detail = [
    path('', include(api_router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('users/subscriptions/', users_subscriptions_view,
         name='subscriptions'),
    path('users/<int:id>/subscribe/', users_subscribe_view, name='subscribe'),
]

urlpatterns = [
    path('', include(urlpatterns_detail)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
