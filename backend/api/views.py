from io import BytesIO

from api.filters import IngredientFilter, RecipeFilter
from api.paginations import PageLimitPagination
from api.serializers import (FavoriteSerializer, IngredientSerializer,
                             RecipeSerializer, ShoppingCartSerializer,
                             TagSerializer, UserSerializer, UserCreateSerializer, ChangePasswordSerializer,
                             SubscriptionsSerializer, TokenSerializer)
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend

from api.tokens import CustomAccessToken
from recipes.models import (FavoriteRecipe, Ingredient, Recipe, ShoppingCart,
                            Tag)
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from rest_framework.response import Response
from rest_framework.status import (HTTP_200_OK, HTTP_201_CREATED,
                                   HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST,
                                   HTTP_401_UNAUTHORIZED)
from rest_framework import mixins, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import IsAuthenticated
from api.permissions import IsAuthor, IsAdminOrReadOnly
from users.models import User, Follow


class TagViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели Tag."""

    queryset = Tag.objects.all()
    permission_classes = (IsAdminOrReadOnly,)
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели Ingredient."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    lookup_field = 'id'


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели Recipe."""

    queryset = Recipe.objects.select_related(
        'author'
    ).prefetch_related(
        'tags', 'ingredients'
    ).order_by('-pub_date').annotate(
        is_favorited=Count('favorite_recipes'),
        is_in_shopping_cart=Count(
            'shopping_carts_recipes'
        )
    )
    serializer_class = RecipeSerializer
    pagination_class = PageLimitPagination
    permission_classes = (IsAuthor,)
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user
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
        recipes = request.user.shopping_carts_recipes.all()

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
            TTFont('Aerial', 'api/Aerial.ttf')
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
            recipe=get_object_or_404(Recipe, id=recipe_id)
        )

    @action(
        detail=False,
        methods=['DELETE'],
        permission_classes=(IsAuthenticated,)
    )
    def destroy_shopping_cart(self, request):
        recipe_id = request.kwargs.get('recipe_id')
        if ShoppingCart.objects.filter(
            user=self.request.user,
            recipe=get_object_or_404(Recipe, id=recipe_id)
        ).delete()[0]:
            return Response(
                {'message': 'Рецепт удален из списка покупок.'},
                status=204
            )
        return Response(
            {'message', 'Рецепт не добавлен в список покупок.'},
            status=400
        )


class FavoriteViewSet(viewsets.ModelViewSet):
    """Вьюсет для списка покупок."""

    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated,)
    queryset = FavoriteRecipe.objects.all()
    lookup_field = 'recipe_id'

    def perform_create(self, serializer):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
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
        if FavoriteRecipe.objects.filter(
            user=self.request.user,
            recipe=get_object_or_404(Recipe, id=recipe_id)
        ).delete()[0]:
            return Response(
                {'message': 'Рецепт удален из избранного.'},
                status=204
            )
        return Response(
            {'message', 'Рецепт не добавлен в избранное.'},
            status=400
        )


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет пользователей."""

    queryset = User.objects.annotate(
        recipes_count=Count('recipes'),
        is_subscribed=Count('following')
    )
    serializer_class = UserSerializer
    pagination_class = PageLimitPagination

    def perform_create(self, serializer):
        serializer.is_valid(raise_exception=True)
        if 'password' not in self.request.data:
            return Response(
                {'message': 'Не передан пароль.'},
                status=HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return Response(serializer.data, status=HTTP_201_CREATED)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer

    @action(
        ['GET'],
        url_path='me',
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def get_data_me(self, request):
        serializer = UserSerializer(
            request.user,
            context={'request': request}
        )
        return Response(
            serializer.data,
            status=HTTP_200_OK
        )

    @action(
        ['POST'],
        url_path='set_password',
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(request.data['current_password']):
            return Response(
                {'message': 'Неверный пароль.'},
                status=HTTP_400_BAD_REQUEST
            )
        request.user.set_password(request.data['new_password'])
        request.user.save()
        return Response(
            {'message': 'Пароль успешно изменен.'},
            status=HTTP_204_NO_CONTENT
        )

    @action(
        ['POST', 'DELETE'],
        detail=True,
        permission_classes=(IsAuthenticated,),
        url_path='subscribe'
    )
    def subscribe(self, request, pk):
        if request.method == 'POST':
            user = get_object_or_404(User.objects.annotate(
                recipes_count=Count('recipes'),
                is_subscribed=Count('following')
            ), id=pk)
            serializer = SubscriptionsSerializer(
                user,
                context={'request': request}
            )
            if request.user == user:
                return Response(
                    {'message': 'Нельзя подписаться на себя.'},
                    status=HTTP_400_BAD_REQUEST
                )
            Follow.objects.get_or_create(
                user=request.user,
                following=user
            )
            return Response(serializer.data, status=HTTP_201_CREATED)
        if request.method == 'DELETE':
            if Follow.objects.filter(
                    user=request.user,
                    following=get_object_or_404(User, id=pk)
            ).delete()[0]:
                return Response(
                    {'message': 'Подписка удалена.'},
                    status=HTTP_204_NO_CONTENT
                )
            else:
                return Response(
                    {'message': 'Вы не подписаны.'},
                    status=HTTP_400_BAD_REQUEST
                )
        return Response(status=HTTP_400_BAD_REQUEST)

    @action(
        ['GET'],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions'
    )
    def get_subscriptions(self, request):
        queryset = User.objects.filter(
            following__user=request.user
        ).order_by('id').annotate(
            recipes_count=Count('recipes'),
            is_subscribed=Count('following')
        )
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(
            page,
            context={'request': request},
            many=True
        )
        return self.get_paginated_response(
            data=serializer.data
        )


@api_view(['POST'])
def get_token(request):
    """Получение токена авторизации."""
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = request.data.get('email')
    user = get_object_or_404(User, email=email)
    return Response(
        {'auth_token': str(CustomAccessToken.for_user(user))},
        status=HTTP_200_OK
    )


@api_view(['POST'])
def logout(request):
    """Выход из системы."""
    if not request.user.is_authenticated:
        return Response(
            {'message': 'Пользователь не авторизован.'},
            status=HTTP_401_UNAUTHORIZED
        )
    request.auth.blacklist()
    return Response(
        {'message': 'Вы вышли из системы.'},
        status=HTTP_204_NO_CONTENT
    )
