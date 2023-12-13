from django.db.models import Count
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
    IngredientSerializer, FavoriteSerializer
)
from recipes.models import Tag, Recipe, ShoppingCart, Ingredient, FavoritesRecipes, IngredientAmount
from users.models import User


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


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели Recipe."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = LimitOffsetPagination

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user
        )


class ShoppingCartViewSet(viewsets.ModelViewSet):
    """Вьюсет для списка покупок."""

    serializer_class = ShoppingCartSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = 'recipe_id'

    def get_recipe(self):
        recipe_id = self.kwargs.get('recipe_id')
        return get_object_or_404(Recipe, id=recipe_id)

    def get_queryset(self):
        return self.get_recipe().shopping_carts.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, recipe=self.get_recipe())

    @action(
        detail=False,
        methods=['DELETE']
    )
    def destroy_shopping_cart(self):
        ShoppingCart.objects.filter(
            user=self.request.user,
            recipe=self.get_recipe()
        ).delete()


class FavoriteViewSet(viewsets.ModelViewSet):
    """Вьюсет для списка покупок."""

    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = 'recipe_id'

    def get_recipe(self):
        recipe_id = self.kwargs.get('recipe_id')
        return get_object_or_404(Recipe, id=recipe_id)

    def get_queryset(self):
        return self.get_recipe().favorite_recipes.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, recipe=self.get_recipe())

    @action(
        detail=False,
        methods=['DELETE']
    )
    def destroy_favorite(self):
        FavoritesRecipes.objects.filter(
            user=self.request.user,
            recipe=self.get_recipe()
        ).delete()
