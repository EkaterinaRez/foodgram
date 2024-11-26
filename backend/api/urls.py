from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView

from api.views import FavoriteViewSet, FoodgramUserViewSet

api_router = DefaultRouter()
api_router.register('favorite', FavoriteViewSet, basename='favorites')
api_router.register(r'users', FoodgramUserViewSet, basename='users')
# api_v1_router.register(
#     r'posts/(?P<post_id>\d+)/comments',
#     CommentViewSet,
#     basename='post-comments'
# )


urlpatterns_detail = [
    path('', include(api_router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    # path('auth/token/login/', TokenObtainPairView.as_view(),
    #      name='token_obtain_pair'),
]
urlpatterns = [
    path('', include(urlpatterns_detail)),
]
