from django.conf import settings
from django.db import models as d_models
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.pdfgen import canvas
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core.generator import generate_short_url
from core.filters import IngredientFilter, RecipeFilter
from core.paginations import ApiPagination
from core.permissions import IsAuthAuthorOrReadonly
from recipes.models import (Favorite, Ingredient, IngredientForRecipe, Recipe,
                            ShoppingCart, Tag)
from shortlink.models import UrlShort
from users.models import FoodgramUser, Subscription
from .serializers import (FavoriteSerializer, FoodgramUserSerializer,
                          IngredientSerializer, PasswordChangeSerializer,
                          RecipeReadSerializer, RecipeWriteSerializer,
                          ShoppingCartSerializer, SubscriptionSerializer,
                          TagSerializer)


class FoodgramUserViewSet(viewsets.ModelViewSet):
    """Вьюсет для управления пользователями."""

    queryset = FoodgramUser.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    search_fields = ("username",)
    http_method_names = ("get", "post", "put", "delete")
    lookup_field = "id"
    pagination_class = ApiPagination

    @action(
        detail=False,
        methods=("get", "patch"),
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

    @action(detail=True,
            methods=['post', 'delete'],
            url_path='subscribe',)
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

    def get_permissions(self):
        if self.action in ('create', 'list', 'retrieve'):
            self.permission_classes = (AllowAny,)
        return super(FoodgramUserViewSet, self).get_permissions()

    def get_serializer_class(self):
        if self.action in ('subscribe', 'list_subscriptions'):
            return SubscriptionSerializer
        return FoodgramUserSerializer

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
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = ApiPagination

    def get_queryset(self):
        user = self.request.user
        query = Recipe.objects

        prefetch_subs = d_models.Prefetch(
            'author__subscribers',
            queryset=Subscription.objects.all().annotate(
                is_subscribed=d_models.Exists(
                    Subscription.objects.filter(
                        author=d_models.OuterRef('author'),
                        user_id=user.id,
                    )
                ) if user.is_authenticated else d_models.Value(
                    False,
                    output_field=d_models.BooleanField()
                )
            ),
            to_attr='subs',
        )

        query = query.select_related('author').prefetch_related(
            'recipe_ingredients__ingredient',
            'recipe_ingredients',
            'tags',
            prefetch_subs,
        )

        if user.is_authenticated:
            query = query.annotate(
                is_favorited=d_models.Exists(
                    Favorite.objects.filter(
                        user_id=user.id, recipe=d_models.OuterRef('pk')
                    )
                ),
                is_in_shopping_cart=d_models.Exists(
                    ShoppingCart.objects.filter(
                        user_id=user.id, recipe=d_models.OuterRef('pk')
                    )
                ),
            )
        else:
            query = query.annotate(
                is_favorited=d_models.Value(
                    False, output_field=d_models.BooleanField()),
                is_in_shopping_cart=d_models.Value(
                    False, output_field=d_models.BooleanField()),
            )

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

    def is_favorited_by(self, user):
        if not user.is_authenticated:
            return False
        return Favorite.objects.filter(user=user, recipe=self).exists()

    def create(self, request, *args, **kwargs):
        write_serializer = self.get_serializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        recipe = write_serializer.save()

        read_serializer = RecipeReadSerializer(
            recipe, context={'request': request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        write_serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        write_serializer.is_valid(raise_exception=True)
        recipe = write_serializer.save()
        read_serializer = RecipeReadSerializer(
            recipe, context={'request': request})

        return Response(read_serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=['get'],
            url_path='get-link',
            permission_classes=[AllowAny])
    def get_link(self, request, pk=None):
        base_url = getattr(settings, 'DOMAIN_URL', 'http://localhost:8000')
        long_url = f'{base_url}/recipes/{pk}/'
        full_url_short = f'{base_url}/s/{generate_short_url}'
        full_url_short, created = UrlShort.objects.get_or_create(
            long_url=long_url)
        return Response({"short-link": full_url_short})

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite')
    def favorite(self, request, *args, **kwargs):
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

    @action(detail=True,
            methods=['post', 'delete'],
            url_path='shopping_cart'
            )
    def shopping_cart(self, request, pk=None):
        """Добавление и удаление рецепта в корзине."""

        if request.method == 'POST':
            recipe = get_object_or_404(Recipe, pk=pk)
            cart_item, created = ShoppingCart.objects.get_or_create(
                user=request.user, recipe=recipe
            )
            if created:
                serializer = ShoppingCartSerializer(cart_item)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {'status': 'Рецепт уже в корзине.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, pk=pk)
        try:
            cart_item = ShoppingCart.objects.get(
                user=request.user, recipe=recipe)
            cart_item.delete()
            return Response(
                {'status': 'Рецепт удалён из корзины.'},
                status=status.HTTP_204_NO_CONTENT
            )
        except ShoppingCart.DoesNotExist:
            return Response(
                {'status': 'Рецепта в корзине нет.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False,
            methods=['get'],
            url_path='download_shopping_cart'
            )
    def download_shopping_list(self, request):
        """Скачивание корзины в pdf."""

        user_id = request.user.id
        ingredients = (
            IngredientForRecipe.objects
            .filter(recipe__shopping_cart__user_id=user_id)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=d_models.Sum('amount'))
        )
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.pdf"')

        pdf_file = canvas.Canvas(response)
        y_position = 800
        pdf_file.drawString(100, y_position, "Список покупок:")
        y_position -= 25

        for item in ingredients:
            ingredient_name = item['ingredient__name']
            measurement_unit = item['ingredient__measurement_unit']
            total_amount = item['total_amount']

            line = f"- {ingredient_name}: {total_amount} {measurement_unit}"
            pdf_file.drawString(100, y_position, line)
            y_position -= 20

        pdf_file.save()
        return response
