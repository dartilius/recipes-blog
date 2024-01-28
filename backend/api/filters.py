from django_filters.rest_framework import (CharFilter, FilterSet,
                                           AllValuesMultipleFilter)
from recipes.models import Ingredient, Recipe
from users.models import User


class RecipeFilter(FilterSet):
    """Фильтры для рецептов."""

    is_in_shopping_cart = CharFilter(method='get_is_in_shopping_cart')
    is_favorited = CharFilter(method='get_is_favorited')
    author = CharFilter(field_name='author__id')
    tags = AllValuesMultipleFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = ('is_in_shopping_cart', 'is_favorited', 'author', 'tags')

    def get_is_in_shopping_cart(self, queryset, name, value):
        if value == '1' and self.request.user.is_authenticated:
            return self.request.user.recipes_is_in_shopping_cart.all()
        elif value == '0':
            return queryset.filter(is_in_shopping_cart=None)
        else:
            return queryset

    def get_is_favorited(self, queryset, name, value):
        if value == '1' and self.request.user.is_authenticated:
            return self.request.user.recipes_is_favorited.all()
        elif value == '0':
            return queryset.filter(is_favorited=None)
        else:
            return queryset


class IngredientFilter(FilterSet):
    """Фильтрация ингредиентов."""

    name = CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
