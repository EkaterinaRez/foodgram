from django.contrib import admin

from .models import (Favorite,
                     Ingredient,
                     IngredientForRecipe,
                     Recipe,
                     ShoppingCart,
                     Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


class IngredientsInline(admin.TabularInline):
    model = IngredientForRecipe
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'total_favorites')
    list_filter = ('author__first_name', 'name', 'tags__slug')
    search_fields = ('name', 'author__first_name', 'tags__slug')
    inlines = [IngredientsInline]
    autocomplete_fields = ('ingredients', 'tags')

    def total_favorites(self, obj):
        """Отображает сколько раз добавили в избранное рецептов."""

        return Favorite.objects.filter(recipe=obj).count()

    total_favorites.short_description = 'Всего добавлено в избранное'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
