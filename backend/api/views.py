
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from core.filters import IngredientFilter, RecipeFilter
from core.paginations import ApiPagination
from core.permissions import IsAdminOrReadOnly
from recipes.models import Favorite, Ingredient, Tag, Recipe
from .serializers import (FavoriteSerializer,
                          FoodgramUserSerializer,
                          IngredientSerializer,
                          RecipeReadSerializer,
                          RecipeWriteSerializer,
                          TagSerializer
                          )
from users.models import FoodgramUser


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
        """Загрузка аватара текущего пользователя."""

        user = request.user
        file = request.FILES.get('avatar')
        if not file:
            return Response({"detail": "Нет файла."},
                            status=status.HTTP_400_BAD_REQUEST
                            )

        user.avatar = file
        user.save()
        return Response({"detail": "Аватар загружен."},
                        status=status.HTTP_200_OK
                        )

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

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для управления ингредиентами рецептов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filterset_class = IngredientFilter
    permission_classes = (AllowAny,)


class FavoriteViewSet(viewsets.ModelViewSet):
    """Вьюсет для управления избранными рецептами."""

    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для управления рецептами."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filterset_class = RecipeFilter
    pagination_class = ApiPagination

    # def get_serializer_context(self):
    #     context = super().get_serializer_context()
    #     context['request'] = self.request
    #     return context

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        write_serializer = self.get_serializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        recipe = write_serializer.save()

        read_serializer = RecipeReadSerializer(
            recipe, context={'request': request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if request.user != instance.author:
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user != instance.author:
            return Response(status=status.HTTP_403_FORBIDDEN)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        short_link = f"https://clck.ru//{pk}"
        return Response({'short_link': short_link})
