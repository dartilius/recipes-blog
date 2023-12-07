from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from requests import Response
from rest_framework import viewsets, mixins, filters
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated

from api.serializers import (
    TagSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    IngredientSerializer
)
from recipes.models import Tag, Recipe, ShoppingCart, Ingredient


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """Вьюсет для модели Tag."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели Ingredient."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('name',)
    filterset_fields = ('name',)
    lookup_field = 'name'


class RecipeViewSet(
    viewsets.ModelViewSet
):
    """Вьюсет для модели Recipe."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = LimitOffsetPagination

    @action(
        ['POST', 'DELETE'],
        url_path='shopping_cart',
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        serializer = ShoppingCartSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        if request.method == 'POST':
            serializer.save(
                user=self.request.user,
                recipe=get_object_or_404(
                    Recipe,
                    id=pk
                )
            )

        if request.method == 'DELETE':
            ShoppingCart.objects.filter(
                user=request.user,
                recipe=get_object_or_404(
                    Recipe,
                    id=pk
                )
            ).delete()


class ShoppingCartViewSet(viewsets.ModelViewSet):
    """Вьюсет для списка покупок."""

    serializer_class = ShoppingCartSerializer
    permission_classes = (IsAuthenticated,)

    def get_recipe(self):
        recipe_id = self.kwargs.get('recipe_id')
        return get_object_or_404(Recipe, id=recipe_id)

    def get_queryset(self):
        return self.get_recipe().shopping_carts.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, recipe=self.get_recipe())
