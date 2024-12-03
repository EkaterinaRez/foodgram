from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe


class IngredientFilter(filters.FilterSet):
    """Фильтр для ингредиентов рецептов."""

    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeFilter(filters.FilterSet):
    is_favorite = filters.BooleanFilter(method='filter_is_favorite')
    is_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')
    author = filters.NumberFilter(field_name='author__id')
    tags = filters.CharFilter(
        field_name='tags__slug', lookup_expr='icontains')

    class Meta:
        model = Recipe
        fields = ['is_favorite', 'is_shopping_cart', 'author', 'tags']

    def filter_is_favorite(self, queryset, name, value):
        if value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset.exclude(favorites__user=self.request.user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset.exclude(shopping_cart__user=self.request.user)
