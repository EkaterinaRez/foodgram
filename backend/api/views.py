from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import models as d_models
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser import views as djoser_views
from djoser import serializers as djoser_serializers
from io import BytesIO
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, IngredientForRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import User, Subscription
from .filters import IngredientFilter, RecipeFilter
from .paginations import ApiPagination
from .permissions import IsAuthAuthorOrReadonly
from .serializers import (FavoriteSerializer, UserSerializer,
                          IngredientSerializer,
                          RecipeReadSerializer, RecipeWriteSerializer,
                          ShoppingCartSerializer, ShortRecipeSerializer,
                          SubscriptionSerializer, TagSerializer)


class UserViewSet(djoser_views.UserViewSet):
    """Вьюсет для управления пользователями."""

    queryset = User.objects.all()
    filter_backends = (DjangoFilterBackend,)
    search_fields = ('username',)
    http_method_names = ('get', 'post', 'put', 'delete')
    lookup_field = 'id'
    pagination_class = ApiPagination

    def get_permissions(self):
        if self.action in ('create', 'list', 'retrieve'):
            self.permission_classes = (AllowAny,)
        return super(UserViewSet, self).get_permissions()

    def get_serializer_class(self):
        if self.action in ('subscribe', 'list_subscriptions'):
            return SubscriptionSerializer
        elif self.action == 'set_password':
            return djoser_serializers.SetPasswordSerializer
        return UserSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(
        detail=False,
        methods=('put', 'delete'),
        url_path='me/avatar'
    )
    def avatar(self, request):
        """Изменение и удаление аватара текущего пользователя."""
        user = request.user
        if request.method == 'PUT':
            data = request.data.get('avatar')
            serializer = self.get_serializer(
                user, data={'avatar': data}, partial=True)
            if serializer.is_valid():
                serializer.save()
                base_url = getattr(settings,
                                   'DOMAIN_URL',
                                   'http://localhost:8000'
                                   )
                return Response(
                    {'avatar': f'{base_url}/{user.avatar}'},
                    status=status.HTTP_200_OK
                )
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST
                            )

        elif request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response({'detail': 'Аватар удалён.'},
                            status=status.HTTP_204_NO_CONTENT
                            )

    @action(detail=True,
            methods=['post', 'delete'],
            url_path='subscribe')
    def subscribe(self, request, id):
        """Управление подписками."""
        author = get_object_or_404(User, id=id)
        user = request.user

        if request.method == 'POST':
            data = {'author': author.id, 'user': user.id}
            serializer = SubscriptionSerializer(
                data=data, context={'request': request})

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED
                                )
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST
                            )

        if request.method == 'DELETE':
            deleted_count, _ = Subscription.objects.filter(
                user=user,
                author=author
            ).delete()

        if deleted_count > 0:
            return Response(
                {'status': 'Подписка удалена.'},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {'status': 'Подписка не существует.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False,
            methods=['get'],
            url_path='subscriptions')
    def list_subscriptions(self, request):
        """Получаем свой список подписок."""
        user = request.user
        subscriptions = Subscription.objects.filter(
            user=user).select_related(
                'author').annotate(
            recipes_count=d_models.Count('author__recipes')
        )

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


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для управления тегами рецептов."""

    queryset = Tag.objects
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для управления ингредиентами рецептов."""

    queryset = Ingredient.objects
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter
    permission_classes = (AllowAny,)


def handle_favorite_or_cart(request,
                            user,
                            recipe,
                            serializer_class,
                            model_class,
                            remove_message):
    """Обработка добавления рецепта в избранное или корзину."""
    if request.method == 'POST':
        serializer_context = {'request': request,
                              'user': user}
        serializer = serializer_class(
            data={'user': user.id, 'recipe': recipe.id},
            context=serializer_context
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save(user=user, recipe=recipe)
            return Response(ShortRecipeSerializer(recipe).data,
                            status=status.HTTP_201_CREATED
                            )
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST
                        )

    if request.method == 'DELETE':
        deleted_count, _ = model_class.objects.filter(
            user=user,
            recipe=recipe
        ).delete()

        if deleted_count > 0:
            return Response(
                {'status': remove_message},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {'status': f'Не найден рецепт в {remove_message.lower()}.'},
            status=status.HTTP_400_BAD_REQUEST
        )


def create_shopping_list_file(user_id):
    """Создание списка покупок для пользователя."""
    ingredients = (
        IngredientForRecipe.objects
        .filter(recipe__shoppingcart_related__user_id=user_id)
        .values('ingredient__name', 'ingredient__measurement_unit')
        .annotate(total_amount=d_models.Sum('amount'))
    )
    buffer = BytesIO()
    buffer.write('Список покупок:\n\n'.encode('utf-8'))

    for item in ingredients:
        ingredient_name = item['ingredient__name']
        measurement_unit = item['ingredient__measurement_unit']
        total_amount = item['total_amount']
        line = f'- {ingredient_name}: {total_amount} {measurement_unit}\n'
        buffer.write(line.encode('utf-8'))

    buffer.seek(0)
    return buffer


def redirect_to_long_url(request, short_url):
    """Редирект на рецепт по короткому ссылке."""
    recipe = get_object_or_404(Recipe, short_url=short_url)
    base_url = getattr(settings, 'DOMAIN_URL', 'http://localhost:8000')
    long_url = f'{base_url}/recipes/{recipe.pk}/'
    return redirect(long_url)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для управления рецептами."""

    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = ApiPagination

    def get_queryset(self):
        prefetch_subs = d_models.Prefetch(
            'author__subscribers',
            queryset=Subscription.objects.annotate(
                is_subscribed=d_models.Exists(
                    Subscription.objects.filter(
                        author=d_models.OuterRef('author'),
                        user=self.request.user.id,
                    )
                ) if self.request.user.is_authenticated else d_models.Value(
                    False,
                    output_field=d_models.BooleanField()
                )
            ),
            to_attr='subs',
        )

        query = Recipe.objects.select_related('author').prefetch_related(
            'recipe_ingredients__ingredient',
            'recipe_ingredients',
            'tags',
            prefetch_subs,
        )

        if self.request.user.is_authenticated:
            query = query.annotate(
                is_favorited=d_models.Exists(
                    Favorite.objects.filter(
                        user=self.request.user.id, recipe=d_models.OuterRef(
                            'pk')
                    )
                ),
                is_in_shopping_cart=d_models.Exists(
                    ShoppingCart.objects.filter(
                        user=self.request.user.id, recipe=d_models.OuterRef(
                            'pk')
                    )
                ),
            )

        author_param = self.request.GET.get('author')
        if author_param == 'me':
            query = query.filter(author=self.request.user.id)

        return query.order_by('-pub_date').all()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_permissions(self):
        if self.action in ('update', 'partial_update', 'destroy'):
            return [IsAuthAuthorOrReadonly()]
        elif self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return super().get_permissions()

    @login_required
    def is_favorited(self, user):
        return Favorite.objects.filter(user=user, recipe=self).exists()

    def perform_create(self, serializer):
        """Возврат данных через другой сериализатор."""
        recipe = serializer.save()
        read_serializer = RecipeReadSerializer(
            recipe, context=self.get_serializer_context())
        return read_serializer.data

    def perform_update(self, serializer):
        """Возврат данных через другой сериализатор."""
        recipe = serializer.save()
        read_serializer = RecipeReadSerializer(
            recipe, context=self.get_serializer_context())
        return read_serializer.data

    @action(detail=True,
            methods=['get'],
            url_path='get-link',
            permission_classes=[AllowAny])
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        base_url = getattr(settings, 'DOMAIN_URL', 'http://localhost:8000')
        if not recipe.short_url:
            recipe.save()
        full_short_url = f'{base_url}/s/{recipe.short_url}'

        return Response({'short-link': full_short_url})

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite')
    def favorite(self, request, *args, **kwargs):
        user = request.user
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('pk'))

        return handle_favorite_or_cart(
            request=request,
            user=user,
            recipe=recipe,
            serializer_class=FavoriteSerializer,
            model_class=Favorite,
            remove_message='Рецепт удалён из избранного.'
        )

    @action(detail=True,
            methods=['post', 'delete'],
            url_path='shopping_cart'
            )
    def shopping_cart(self, request, pk=None):
        """Добавление и удаление рецепта в корзине."""
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        return handle_favorite_or_cart(
            request=request,
            user=user,
            recipe=recipe,
            serializer_class=ShoppingCartSerializer,
            model_class=ShoppingCart,
            remove_message='Рецепт удалён из корзины.'
        )

    @action(detail=False,
            methods=['get'],
            url_path='download_shopping_cart'
            )
    def download_shopping_list(self, request):
        """Скачивание корзины в файл."""
        user_id = request.user.id
        shopping_list_buffer = create_shopping_list_file(user_id)
        response = HttpResponse(shopping_list_buffer,
                                content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = (
            'attachment;filename="shopping_list.txt"')
        return response
