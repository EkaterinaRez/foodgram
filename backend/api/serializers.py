
import base64
from django.core.files.base import ContentFile
from rest_framework import serializers

from recipes.models import (Favorites, Ingredients, IngredientsForRecipe,
                            Recipes, ShoppingCart, Tags)
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
        model = Tags
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredients
        fields = ('id', 'name', 'measurement_unit')


class IngredientsForRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов для рецепта."""
    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True)

    class Meta:
        model = IngredientsForRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientsForRecipePostSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления ингредиентов."""
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientsForRecipe
        fields = ('id', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для метода get рецепта."""

    author = FoodgramUserSerializer(read_only=True)
    ingredients = IngredientsForRecipePostSerializer(
        source='recipe_ingredients', many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipes
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    # def get_author(self, obj):
    #     user = obj.author
    #     return {
    #         "email": user.email,
    #         "id": user.id,
    #         "username": user.username,
    #         "first_name": user.first_name,
    #         "last_name": user.last_name,
    #         "is_subscribed": user.False,
    #         "avatar": "http://foodgram.example.org/media/users/image.png"  # Placeholder
    #     }

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return Favorites.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для методов post/patch/put/delete рецепта."""

    ingredients = IngredientsForRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tags.objects.all())
    image = Base64ImageField()

    class Meta:
        model = Recipes
        fields = ('id', 'ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time')

    def create(self, validated_data):
        print(validated_data)
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        author = self.context['request'].user
        recipe = Recipes.objects.create(author=author, **validated_data)

        for ingredient in ingredients_data:
            IngredientsForRecipe.objects.create(
                recipe=recipe,
                id=ingredient['ingredients']['id'],
                amount=ingredient['amount']
            )

        for tag in tags_data:
            recipe.tags.add(tag)

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)

        instance = super().update(instance, validated_data)

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            for ingredient in ingredients_data:
                IngredientsForRecipe.objects.create(
                    recipe=instance,
                    ingredient_id=ingredient['ingredient']['id'],
                    amount=ingredient['amount']
                )

        if tags_data is not None:
            instance.tags.set(tags_data)

        return instance


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранных рецептов."""
    user = serializers.SlugRelatedField(
        slug_field='username', queryset=FoodgramUser.objects.all()
    )
    recipe = serializers.SlugRelatedField(
        queryset=Recipes.objects.all(),
        slug_field='name'
    )

    class Meta:
        model = Favorites
        fields = ('id', 'user', 'recipe')


class ShoppingCartSerializer(serializers.ModelSerializer):
    recipe = serializers.SlugRelatedField(
        queryset=Recipes.objects.all(),
        slug_field='name'
    )

    class Meta:
        model = ShoppingCart
        fields = ('id', 'user', 'recipe')
