from django_filters.rest_framework import (CharFilter, FilterSet,
                                           MultipleChoiceFilter)

from recipes.models import Ingredient, Recipe, Tag
from users.models import User


class AllTagValuesFilter(MultipleChoiceFilter):
    """Фильтрация по всем полям модели."""
    @property
    def field(self):
        qs = Tag._default_manager.distinct()
        qs = qs.order_by('slug').values_list('slug', flat=True)
        self.extra["choices"] = [(o, o) for o in qs]
        return super().field


class RecipeFilter(FilterSet):
    """Фильтры для произведений."""

    is_in_shopping_cart = CharFilter(method='get_is_in_shopping_cart')
    is_favorited = CharFilter(method='get_is_favorited')
    author = CharFilter(field_name='author__id')
    tags = AllTagValuesFilter(field_name='tags__slug')

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


class UserFilter(FilterSet):
    """Фильтрация пользователей."""

    first_name = CharFilter(field_name='first_name', lookup_expr='iexact')
    email = CharFilter(field_name='email', lookup_expr='iexact')

    class Meta:
        model = User
        fields = ('first_name', 'email')
