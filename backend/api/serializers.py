from rest_framework import serializers

from recipes.models import (Favorites, Ingredients, IngredientsForRecipe,
                            Recipes, ShoppingCart, Tags)
from users.models import FoodgramUser


class FoodgramUserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователей"""

    class Meta:
        model = FoodgramUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name')


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

    ingredient = IngredientSerializer(read_only=True)
    ingredient_id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredients.objects.all(),
        source='ingredient',
        write_only=True
    )
    count = serializers.IntegerField()

    class Meta:
        model = IngredientsForRecipe
        fields = ('ingredient', 'ingredient_id', 'count')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов."""

    author = serializers.SlugRelatedField(
        slug_field='username', queryset=FoodgramUser.objects.all()
    )
    ingredients = IngredientsForRecipeSerializer(
        source='recipe_ingredients', many=True
    )
    tags = TagSerializer(many=True)
    image = serializers.ImageField(required=False)

    class Meta:
        model = Recipes
        fields = (
            'id', 'author', 'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time', 'pub_date'
        )

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipes.objects.create(**validated_data)

        for ingredient_data in ingredients_data:
            IngredientsForRecipe.objects.create(
                recipe=recipe,
                **ingredient_data
            )

        recipe.tags.set(tags_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients', None)
        tags_data = validated_data.pop('tags', None)

        instance = super().update(instance, validated_data)

        if ingredients_data:
            instance.recipe_ingredients.all().delete()
            for ingredient_data in ingredients_data:
                IngredientsForRecipe.objects.create(
                    recipe=instance,
                    **ingredient_data
                )

        if tags_data:
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
