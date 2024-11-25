from django.contrib import admin

from .models import (Favorites,
                     Ingredients,
                     IngredientsForRecipe,
                     Recipes,
                     ShoppingCart,
                     Tags)


@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredients)
class IngredientsAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


class IngredientsInline(admin.TabularInline):
    model = IngredientsForRecipe
    extra = 1


@admin.register(Recipes)
class RecipesAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'total_favorites')
    list_filter = ('author__username', 'name', 'tags__slug')
    search_fields = ('name', 'author__username', 'tags__slug')
    inlines = [IngredientsInline]
    autocomplete_fields = ('ingredients', 'tags')

    def total_favorites(self, obj):
        """Отображает сколько раз добавили в избранное рецептов."""

        return Favorites.objects.filter(recipe=obj).count()

    total_favorites.short_description = 'Total Favorites'


@admin.register(Favorites)
class FavoritesAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
