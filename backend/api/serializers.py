import base64
from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, IngredientForRecipe,
                            Recipe, ShoppingCart, Tag)
from users.models import FoodgramUser, Subscription


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class FoodgramUserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователей"""
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = FoodgramUser
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'is_subscribed', 'avatar', 'password')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = FoodgramUser(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def get_is_subscribed(self, obj):
        """Проверка подписки на автора."""

        user = self.context['request'].user
        if user.is_authenticated:
            return Subscription.objects.filter(user=user, author=obj).exists()
        return False

    def to_representation(self, instance):
        represent = super().to_representation(instance)
        if self.context['request'].method == 'POST':
            represent.pop('is_subscribed', None)
            represent.pop('avatar', None)

        return represent


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientForRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов для рецепта."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all())
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True)
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientForRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для метода get рецепта."""

    author = serializers.SerializerMethodField()
    ingredients = IngredientForRecipeSerializer(
        source='recipe_ingredients', many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def get_author(self, obj):
        """Определяем поля для вывода об авторе рецепта."""

        user = obj.author
        request_user = self.context['request'].user
        is_subscribed = False

        if request_user.is_authenticated:
            is_subscribed = user.subscribers.filter(
                id=request_user.id).exists()

        return {
            "email": user.email,
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_subscribed": is_subscribed,
            "avatar": user.avatar.url if user.avatar else None
        }

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для методов post/patch/put/delete рецепта."""

    ingredients = IngredientForRecipeSerializer(many=True, write_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    image = Base64ImageField(write_only=True, allow_null=True)

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time')

    def create_ingredient(self, ingredients, recipe):
        for ingredient in ingredients:
            print('ingredient', ingredient)
            amount = ingredient['amount']
            ingredient = ingredient['id']
            ingredients, created = IngredientForRecipe.objects.get_or_create(
                recipe=recipe,
                ingredient=ingredient,
                amount=amount
            )

    def validate_ingredient(self, value):
        if not value:
            raise serializers.ValidationError(
                "Необходимо указать хотя бы один ингредиент.")
        unique_Ingredient = set()
        for item in value:
            if item['ingredient'] in unique_Ingredient:
                raise serializers.ValidationError(
                    "Ингредиенты должны быть уникальными.")
            unique_Ingredient.add(item['ingredient'])
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                "Необходимо указать хотя бы один тег.")
        return value

    @ transaction.atomic
    def create(self, validated_data):
        print('################################', validated_data)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['author'] = request.user

        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        recipe.save()
        self.create_ingredient(ingredients, recipe)
        return recipe

    # def update(self, instance, validated_data):
    #     Ingredient_data = validated_data.pop('Ingredient', None)
    #     tags_data = validated_data.pop('tags', None)

    #     instance = super().update(instance, validated_data)

    #     if Ingredient_data is not None:
    #         instance.recipe_Ingredient.all().delete()
    #         for ingredient in Ingredient_data:
    #             IngredientForRecipe.objects.create(
    #                 recipe=instance,
    #                 ingredient_id=ingredient['id'],
    #                 amount=ingredient['amount']
    #             )

    #     if tags_data is not None:
    #         instance.tags.set(tags_data)

    #     return instance


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранных рецептов."""
    user = serializers.SlugRelatedField(
        slug_field='username', queryset=FoodgramUser.objects.all()
    )
    recipe = serializers.SlugRelatedField(
        queryset=Recipe.objects.all(),
        slug_field='name'
    )

    class Meta:
        model = Favorite
        fields = ('id', 'user', 'recipe')


class ShoppingCartSerializer(serializers.ModelSerializer):
    recipe = serializers.SlugRelatedField(
        queryset=Recipe.objects.all(),
        slug_field='name'
    )

    class Meta:
        model = ShoppingCart
        fields = ('id', 'user', 'recipe')
