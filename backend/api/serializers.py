import base64

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from django.db import transaction

from recipes.models import (Favorite, Ingredient, IngredientForRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework import serializers
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


class PasswordChangeSerializer(serializers.Serializer):
    """Сериализатор для смены пароля."""

    new_password = serializers.CharField(required=True, write_only=True)
    current_password = serializers.CharField(required=True, write_only=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Неправильный старый пароль.')
        return value

    def validate_new_password(self, value):
        validate_password(value, self.context['request'].user)
        return value


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

    # def get_author(self, obj):
    #     """Определяем поля для вывода об авторе рецепта."""

    #     user = obj.author
    #     request_user = self.context['request'].user
    #     is_subscribed = False

    #     if request_user.is_authenticated:
    #         is_subscribed = user.subscribers.filter(
    #             id=request_user.id).exists()

    #     return {
    #         "email": user.email,
    #         "id": user.id,
    #         "username": user.username,
    #         "first_name": user.first_name,
    #         "last_name": user.last_name,
    #         "is_subscribed": is_subscribed,
    #         "avatar": user.avatar.url if user.avatar else None
    #     }


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
        unique_tags = set()
        for item in value:
            if item in unique_tags:
                raise serializers.ValidationError(
                    "Теги должны быть уникальными.")
            unique_tags.add(item)
        return value

    @ transaction.atomic
    def create(self, validated_data):
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

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if tags is not None:
            instance.tags.set(tags)
        else:
            raise serializers.ValidationError(
                "Укажите теги.")

        if ingredients is not None:
            instance.ingredients.clear()
            self.create_ingredient(ingredients, instance)
        else:
            raise serializers.ValidationError(
                "Укажите ингредиенты.")

        instance.save()
        return instance


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранных рецептов."""

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
        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time')

    def validate(self, attrs):
        user = self.context['request'].user
        recipe_id = self.context['view'].kwargs.get('pk')

        if Favorite.objects.filter(
                user=user,
                recipe_id=recipe_id).exists():
            raise serializers.ValidationError({'id': 'Рецепт уже добавлен!'})

        return attrs


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписки на авторов."""

    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes',
                  'recipes_count', 'avatar'
                  )

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
        limit = request.GET.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj.author)

        if limit:
            limit = int(limit)
            recipes = recipes[:limit]

        recipes_list = [
            {
                "id": recipe.id,
                "name": recipe.name,
                "image": request.build_absolute_uri(recipe.image.url),
                "cooking_time": recipe.cooking_time
            }
            for recipe in recipes
        ]

        return recipes_list

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()

    def get_avatar(self, obj):
        if obj.author.avatar:
            return f"{settings.MEDIA_URL}{obj.author.avatar}"
        return None


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
