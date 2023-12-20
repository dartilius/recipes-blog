from io import BytesIO

from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from requests import Response
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from api.filters import IngredientFilter, RecipeFilter
from api.paginations import PageLimitPagination
from api.serializers import (FavoriteSerializer, IngredientSerializer,
                             RecipeSerializer, ShoppingCartSerializer,
                             TagSerializer)
from recipes.models import (FavoritesRecipes, Ingredient, Recipe, ShoppingCart,
                            Tag)
from users.permissions import IsAuthor


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """Вьюсет для модели Tag."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """Вьюсет для модели Ingredient."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    lookup_field = 'id'


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели Recipe."""

    queryset = Recipe.objects.all().select_related(
        'author'
    ).order_by('-pub_date')
    serializer_class = RecipeSerializer
    pagination_class = PageLimitPagination
    permission_classes = (IsAuthor,)
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        tags = []
        for tag_id in self.request.data['tags']:
            tags.append(Tag.objects.get(id=tag_id))
        serializer.save(
            author=self.request.user,
            tags=tags
        )

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart'
    )
    def get_shopping_cart(self, request):
        """Загрузка списка покупок."""

        X_OFFSET = 100

        ingredients_count = {}
        recipes = request.user.recipes_is_in_shopping_cart.all()

        for recipe in recipes:
            recipe_ingredients = recipe.ingredients.all()
            for ingredient in recipe_ingredients:
                key = str(
                    ingredient.id.name + " " + "("
                    + ingredient.id.measurement_unit + ")"
                )
                if key not in ingredients_count.keys():
                    ingredients_count[key] = ingredient.amount
                else:
                    ingredients_count[key] += ingredient.amount

        buffer = BytesIO()
        p = Canvas(buffer, pagesize=A4)
        pdfmetrics.registerFont(
            TTFont('Aerial', '/app/foodgram/api/Aerial.ttf')
        )
        p.setFont('Aerial', 16)
        y_offset = 800
        for item in ingredients_count.items():
            p.drawString(X_OFFSET, y_offset, item[0] + ": " + str(item[1]))
            y_offset -= 20
            if y_offset <= 20:
                p.showPage()
                p.setFont('Aerial', 16)
                y_offset = 800
        p.showPage()
        p.save()
        buffer.seek(0)
        return FileResponse(
            buffer,
            as_attachment=True,
            filename='shopping_cart.pdf'
        )


class ShoppingCartViewSet(viewsets.ModelViewSet):
    """Вьюсет для списка покупок."""

    serializer_class = ShoppingCartSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ShoppingCart.objects.all()
    lookup_field = 'recipe_id'

    def perform_create(self, serializer):
        recipe_id = self.kwargs.get('recipe_id')
        serializer.save(
            user=self.request.user,
            recipe=Recipe.objects.get(id=recipe_id)
        )

    @action(
        detail=False,
        methods=['DELETE'],
        permission_classes=(IsAuthenticated,)
    )
    def destroy_shopping_cart(self, request):
        recipe_id = request.kwargs.get('recipe_id')
        ShoppingCart.objects.filter(
            user=self.request.user,
            recipe=Recipe.objects.get(id=recipe_id)
        ).delete()


class FavoriteViewSet(viewsets.ModelViewSet):
    """Вьюсет для списка покупок."""

    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated,)
    queryset = FavoritesRecipes.objects.all()
    lookup_field = 'recipe_id'

    def perform_create(self, serializer):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = Recipe.objects.get(id=recipe_id)
        recipe.favorite_count += 1
        recipe.save()
        serializer.save(
            user=self.request.user,
            recipe=recipe
        )

    @action(
        detail=False,
        methods=['DELETE'],
        permission_classes=(IsAuthenticated,)
    )
    def destroy_favorite(self, request):
        recipe_id = request.kwargs.get('recipe_id')
        if not FavoritesRecipes.objects.filter(
            user=self.request.user,
            recipe=Recipe.objects.get(id=recipe_id)
        ).exists():
            return Response('Рецепт не добавлен в избранное.', status=400)
        FavoritesRecipes.objects.filter(
            user=self.request.user,
            recipe=Recipe.objects.get(id=recipe_id)
        ).delete()
        return Response('Рецепт удален из избранного.', status=204)
