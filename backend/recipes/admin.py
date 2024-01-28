from django.contrib import admin
from django.db.models import Count
from recipes.models import (FavoriteRecipe, Ingredient, IngredientAmount,
                            Recipe, ShoppingCart, Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Тег."""

    list_display = ('name', 'slug', 'color')
    search_fields = ('name', 'slug', 'color')
    list_filter = ('name', 'slug', 'color')

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Рецепт."""

    list_display = (
        'author',
        'name',
        'text',
        'cooking_time',
        'favorite_count',
        'pub_date'
    )
    list_filter = ('author__username', 'author__email', 'name', 'text', 'cooking_time')
    search_fields = ('author__username', 'author__email', 'name', 'text', 'cooking_time')

    def get_queryset(self, request):
        return Recipe.objects.annotate(
            favorite_count=Count('favorite_recipes')
        ).all().select_related('author')

    def favorite_count(self, obj):
        return obj.favorite_count


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Ингредиент."""

    list_display = ('name', 'measurement_unit')
    list_filter = ('name', 'measurement_unit')
    search_fields = ('name', 'measurement_unit')

@admin.register(IngredientAmount)
class IngredientAmountAdmin(admin.ModelAdmin):
    """Ингредиенты в рецептах."""

    list_display = ('ingredient', 'recipe', 'amount')
    list_filter = ('ingredient', 'recipe', 'amount')
    search_fields = ('ingredient', 'recipe', 'amount')

    def get_queryset(self, request):
        return IngredientAmount.objects.all().prefetch_related(
            'amount_ingredients', 'amount_recipes'
        )


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    """Избранные рецепты."""

    list_display = ('recipe', 'user')
    list_filter = ('recipe', 'user__username', 'user__email')
    search_fields = ('recipe', 'user__username', 'user__email')

    def get_queryset(self, request):
        return FavoriteRecipe.objects.all().prefetch_related(
            'favorite_users', 'favorite_recipes'
        )


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Списки покупок."""

    list_display = ('recipe', 'user')
    list_filter = ('recipe', 'user__username', 'user__email')
    search_fields = ('recipe', 'user__username', 'user__email')

    def get_queryset(self, request):
        return FavoriteRecipe.objects.all().prefetch_related(
            'shopping_carts_users', 'shopping_carts_recipes'
        )
