from core.filters import IngredientFilter, RecipeFilter
from core.paginations import ApiPagination
from core.permissions import IsAdminOrReadOnly, IsAuthenticatedOr401
from django.conf import settings
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import Favorite, Ingredient, Recipe, Tag
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from shortlink.models import UrlShort
from users.models import FoodgramUser, Subscription

from .serializers import (FavoriteSerializer, FoodgramUserSerializer,
                          IngredientSerializer, PasswordChangeSerializer,
                          RecipeReadSerializer, RecipeWriteSerializer,
                          SubscriptionSerializer, TagSerializer)


class FoodgramUserViewSet(viewsets.ModelViewSet):
    """Вьюсет для управления пользователями."""

    queryset = FoodgramUser.objects.all()
    serializer_class = FoodgramUserSerializer
    permission_classes = (IsAuthenticatedOr401, IsAdminOrReadOnly)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("username",)
    http_method_names = ("get", "post", "put", "delete")
    lookup_field = "id"
    pagination_class = ApiPagination

    @action(
        detail=False,
        methods=("get", "patch"),
        permission_classes=(IsAuthenticatedOr401,),
    )
    def me(self, request):
        """Получение и изменение информации о текущем пользователе."""

        user = request.user

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
        methods=("put", "delete"),
        permission_classes=(IsAuthenticatedOr401,),
        url_path='me/avatar'
    )
    def avatar(self, request):
        """Изменение и удаление аватара текущего пользователя."""

        user = request.user

        if request.method == "PUT":
            data = request.data.get('avatar')
            if not data:
                return Response({"detail": "Аватара нет."},
                                status=status.HTTP_400_BAD_REQUEST
                                )

            serializer = self.get_serializer(
                user, data={'avatar': data}, partial=True)
            if serializer.is_valid():
                serializer.save()
                base_url = getattr(settings,
                                   'DOMAIN_URL',
                                   'http://localhost:8000'
                                   )
                return Response(
                    {"avatar": f"{base_url}/{user.avatar}"},
                    status=status.HTTP_200_OK
                )
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST
                            )

        elif request.method == "DELETE":
            user.avatar.delete(save=True)
            return Response({"detail": "Аватар удалён."},
                            status=status.HTTP_204_NO_CONTENT
                            )

    @action(
        detail=False,
        methods=['post'],
        permission_classes=(IsAuthenticatedOr401,),
        url_path='set_password'
    )
    def set_password(self, request):
        """Изменение пароля текущего пользователя."""

        user = request.user
        serializer = PasswordChangeSerializer(
            data=request.data, context={'request': request})

        if serializer.is_valid():
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = (AllowAny,)
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
    filterset_class = IngredientFilter
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для управления рецептами."""

    queryset = Recipe.objects.all()
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = ApiPagination

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

        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if request.user != instance.author:
            return Response(status=status.HTTP_403_FORBIDDEN)

        write_serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        write_serializer.is_valid(raise_exception=True)
        recipe = write_serializer.save()
        read_serializer = RecipeReadSerializer(
            recipe, context={'request': request})
        return Response(read_serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if request.user != instance.author:
            return Response(status=status.HTTP_403_FORBIDDEN)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        base_url = getattr(settings, 'DOMAIN_URL', 'http://localhost:8000')
        long_url = f'/api/recipes/{pk}/'
        url_short, created = UrlShort.objects.get_or_create(
            long_url=long_url)
        short_url = f"{base_url}/s/{url_short.short_url}"
        return Response({"short-link": short_url})

    @action(detail=True,
            methods=['post', 'delete'],
            url_path='favorite')
    def favorite(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        user = request.user
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('pk'))
        serializer_context = {
            'request': request,
            'view': self,
        }

        if request.method == 'POST':
            serializer = FavoriteSerializer(
                data=request.data,
                context=serializer_context
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save(user=user, recipe=recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED
                                )
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST
                            )

        if request.method == 'DELETE':
            if not Favorite.objects.filter(
                    user=user, recipe=recipe
            ).exists():
                return Response(
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.get(recipe=recipe).delete()
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )


class SubscriptionViewSet(mixins.CreateModelMixin,
                          mixins.DestroyModelMixin,
                          mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    """Вьюсет для управления подписками на авторов."""
    pagination_class = ApiPagination
    permission_classes = (IsAuthenticatedOr401,)

    @action(detail=True,
            methods=['post', 'delete'],
            url_path='subscribe',
            permission_classes=(IsAuthenticatedOr401,),)
    def subscribe(self, request, id=None):
        """Управление подписками."""

        author = get_object_or_404(FoodgramUser, id=id)
        user = request.user

        if request.method == 'POST':
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {"detail": "Такая подписка уже существует."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if author == user:
                return Response(
                    {"detail": "Подписаться на себя нельзя(хоть и хочется)."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription = Subscription.objects.create(
                user=user, author=author)
            serializer = SubscriptionSerializer(
                subscription, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            subscription = Subscription.objects.filter(
                user=user, author=author)
            if subscription:
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            return Response(
                {"detail": "Подписка не найдена."},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False,
            methods=['get'],
            url_path='subscriptions')
    def list_subscriptions(self, request):
        """Получаем свой список подписок."""

        user = request.user
        subscriptions = Subscription.objects.filter(user=user)

        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = SubscriptionSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(
            subscriptions, many=True, context={'request': request}
        )

        return Response(serializer.data)
