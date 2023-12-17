from django_filters.rest_framework import CharFilter, FilterSet, BooleanFilter

from recipes.models import Recipe


class RecipeFilter(FilterSet):
    """Фильтры для произведений."""
    is_in_shopping_cart = CharFilter(method='get_is_in_shopping_cart')
    is_favorited = CharFilter(method='get_is_favorited')
    author = CharFilter(field_name='author__id', lookup_expr='iexact')
    tags = CharFilter(field_name='tags__slug', lookup_expr='iexact')

    class Meta:
        model = Recipe
        fields = ('is_in_shopping_cart', 'is_favorited', 'author', 'tags')

    def get_is_in_shopping_cart(self, queryset, name, value):
        if value == '1':
            return self.request.user.recipes_is_in_shopping_cart.all()
        elif value == '0':
            return queryset.filter(is_in_shopping_cart=None)
        else:
            return queryset

    def get_is_favorited(self, queryset, name, value):
        if value == '1':
            return self.request.user.recipes_is_favorited.all()
        elif value == '0':
            return queryset.filter(is_favorited=None)
        else:
            return queryset