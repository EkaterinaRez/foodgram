from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from core.paginations import ApiPagination
from core.permissions import IsAdminOrReadOnly
from recipes.models import Favorites, Tags
from users.models import FoodgramUser

from .serializers import FavoriteSerializer, FoodgramUserSerializer, TagSerializer


class FoodgramUserViewSet(viewsets.ModelViewSet):
    """Вьюсет для управления пользователями."""

    queryset = FoodgramUser.objects.all()
    serializer_class = FoodgramUserSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsAdminOrReadOnly)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("username",)
    http_method_names = ("get", "post", "patch", "delete")
    lookup_field = "id"
    pagination_class = ApiPagination

    @action(
        detail=False,
        methods=("get", "patch"),
        permission_classes=(IsAuthenticated,),
    )
    def me(self, request):
        """Получение и изменение информации о текущем пользователе."""

        user = request.user
        if user.is_anonymous:
            return Response(
                {"detail": "Авторизуйтесь для доступа в профиль."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        if request.method == "GET":
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        if request.method == "PATCH":
            serializer = self.get_serializer(
                user, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=False,
        methods=("get", "post", "delete", "patch"),
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar'
    )
    def avatar(self, request):
        user = request.user
        file = request.FILES.get('avatar')
        if not file:
            return Response({"detail": "Нет файла."}, status=status.HTTP_400_BAD_REQUEST)

        user.avatar = file
        user.save()
        return Response({"detail": "Аватар загружен."}, status=status.HTTP_200_OK)

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = (AllowAny,)
        else:
            self.permission_classes = (
                IsAuthenticatedOrReadOnly, IsAdminOrReadOnly)
        return super(FoodgramUserViewSet, self).get_permissions()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для управления тегами рецептов."""

    queryset = Tags.objects.all()
    serializer_class = TagSerializer


class FavoriteViewSet(viewsets.ModelViewSet):
    """Вьюсет для управления избранными рецептами."""

    queryset = Favorites.objects.all()
    serializer_class = FavoriteSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
