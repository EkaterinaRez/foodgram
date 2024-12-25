import base64

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from recipes.models import (Favorite, Ingredient, IngredientForRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework import serializers
from users.models import FoodgramUser, Subscription


class Base64ImageField(serializers.ImageField):
    """Сериализатор для картинок."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class FoodgramUserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователей."""

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

    class Meta:
        model = IngredientForRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для метода get рецепта."""

    author = FoodgramUserSerializer(read_only=True)
    ingredients = IngredientForRecipeSerializer(
        source='recipe_ingredients', many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.BooleanField(default=False, read_only=True)
    is_in_shopping_cart = serializers.BooleanField(
        default=False, read_only=True
    )
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )


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
        ingredient_objects = []
        for ingredient in ingredients:
            amount = ingredient['amount']
            ingredient = ingredient['id']
            ingredient_instance = IngredientForRecipe(
                recipe=recipe,
                ingredient=ingredient,
                amount=amount
            )
            ingredient_objects.append(ingredient_instance)

        IngredientForRecipe.objects.bulk_create(ingredient_objects)

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                "Необходимо указать хотя бы один ингредиент.")

        unique_ingredient = set()
        for item in value:
            if item['amount'] <= 0:
                raise serializers.ValidationError(
                    "Количество ингредиентов должно быть больше нуля.")

            if item['id'] in unique_ingredient:
                raise serializers.ValidationError(
                    "Ингредиенты должны быть уникальными.")
            unique_ingredient.add(item['id'])
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                "Необходимо указать хотя бы один тег.")

        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                "Теги должны быть уникальными."
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['author'] = request.user
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredient(ingredients, recipe)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.create_ingredient(ingredients, instance)
        return instance


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранных рецептов."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Короткий сериализатор для отображения рецептов."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписки на авторов."""

    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True, default=0)
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes',
                  'recipes_count', 'avatar'
                  )

    def validate(self, data):
        user = self.context.get('request').user
        author = data['author']

        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError("Такая подписка уже существует.")
        if author == user:
            raise serializers.ValidationError("Подписаться на себя нельзя.")
        return data

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False

        return Subscription.objects.filter(
            user=obj.user,
            author=obj.author
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit', '5')
        recipes = Recipe.objects.filter(author=obj.author)
        limit = int(limit)
        recipes = recipes[:limit]
        recipes_list = [
            {
                "id": recipe.id,
                "name": recipe.name,
                "image": recipe.image.url,
                "cooking_time": recipe.cooking_time
            }
            for recipe in recipes
        ]

        return recipes_list

    def get_avatar(self, obj):
        if obj.author.avatar:
            return f"{settings.MEDIA_URL}{obj.author.avatar}"
        return None

    def create(self, validated_data):
        return Subscription.objects.create(**validated_data)


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор корзины."""

    id = serializers.PrimaryKeyRelatedField(
        source='recipe',
        read_only=True)
    name = serializers.ReadOnlyField(
        source='recipe.name',
        read_only=True)
    image = serializers.ImageField(
        source='recipe.image',
        read_only=True)
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time',
        read_only=True)

    class Meta:
        model = ShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time')
