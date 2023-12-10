from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from recipes.models import Tag, Recipe, Ingredient, ShoppingCart, IngredientAmount

from recipes.models import FavoritesRecipes

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериалайзер пользоватлея."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )
        read_only_fields = ('is_subscribed',)
        model = User

    def get_is_subscribed(self, obj):
        return True


class IngredientAmountSerializer(serializers.ModelSerializer):
    """Сериалайзер для количества ингредиентов в рецепте."""

    class Meta:
        model = IngredientAmount
        fields = ('id', 'amount')


class TagSerializer(serializers.ModelSerializer):
    """Сериалайзер для модели Tag."""

    class Meta:
        fields = ('id', 'name', 'slug', 'color')
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    """Сериалайзер для модели Ingredient."""

    class Meta:
        fields = ('id', 'name', 'measurement_unit')
        model = Ingredient


class RecipeSerializer(serializers.ModelSerializer):
    """Сериалайзер для модели Recipe."""

    author = UserSerializer()
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'text',
            'cooking_time'
        )
        read_only_fields = ('author', 'is_favorited', 'is_in_shopping_cart')
        model = Recipe


    def get_is_favorited(self, obj):
        if not self.context.get('request').user.is_authenticated:
            return False
        return obj.favorite_recipes.filter(
            user=self.context.get('request').user
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        if not self.context.get('request').user.is_authenticated:
            return False
        return obj.shopping_carts.filter(
            user=self.context.get('request').user
        ).exists()


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериалайзер для списка покупок."""

    user = serializers.SlugRelatedField(
        default=serializers.CurrentUserDefault(),
        queryset=User.objects.all(),
        slug_field='username'
    )

    class Meta:
        model = ShoppingCart
        read_only_fields = ('user', 'recipe')
        exclude = ('recipe',)

    def validate(self, data):
        request = self.context.get('request')
        user = request.user
        recipe_id = self.context.get('view').kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if request.method == 'POST':
            if recipe.shopping_carts.filter(user=user, recipe=recipe):
                raise serializers.ValidationError(
                    'Рецепт уже добавлен в список покупок.'
                )
        return data

class FavoriteSerializer(serializers.ModelSerializer):
    """Сериалайзер для списка покупок."""

    user = serializers.SlugRelatedField(
        default=serializers.CurrentUserDefault(),
        queryset=User.objects.all(),
        slug_field='username'
    )

    class Meta:
        model = FavoritesRecipes
        read_only_fields = ('user', 'recipe')
        exclude = ('recipe',)

    def validate(self, data):
        request = self.context.get('request')
        user = request.user
        recipe_id = self.context.get('view').kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if request.method == 'POST':
            if recipe.favorite_recipes.filter(user=user, recipe=recipe):
                raise serializers.ValidationError(
                    'Рецепт уже добавлен в избранное.'
                )
        return data
