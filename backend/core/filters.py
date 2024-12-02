from django_filters import rest_framework as filters
from recipes.models import Ingredients


class IngredientFilter(filters.FilterSet):
    """Фильтр для ингредиентов рецептов."""

    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredients
        fields = ('id', 'name', 'measurement_unit')
