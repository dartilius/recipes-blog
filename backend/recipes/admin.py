from django.contrib import admin
from recipes.models import (FavoritesRecipes, Ingredient, IngredientAmount,
                            IngredientRecipe, Recipe, ShoppingCart, Tag)


class TagAdmin(admin.ModelAdmin):
    """Тег."""

    list_display = ('name', 'slug', 'color')
    search_fields = ('name', 'slug', 'color')
    list_filter = ('name', 'slug', 'color')


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
    list_filter = ('author', 'name', 'text', 'cooking_time')
    search_fields = ('author', 'name', 'text', 'cooking_time')


class IngredientAdmin(admin.ModelAdmin):
    """Ингредиент."""

    list_display = ('name', 'measurement_unit')
    list_filter = ('name', 'measurement_unit')
    search_fields = ('name', 'measurement_unit')


class IngredientAmountAdmin(admin.ModelAdmin):
    """Ингредиент."""

    list_display = ('id', 'amount')
    list_filter = ('id', 'amount')
    search_fields = ('id', 'amount')


class RecipeTagAdmin(admin.ModelAdmin):
    """Теги рецептов."""

    list_display = ('recipe', 'tag')
    list_filter = ('recipe', 'tag')
    search_fields = ('recipe', 'tag')


class IngredientRecipeAdmin(admin.ModelAdmin):
    """Ингредиенты рецептов."""

    list_display = ('recipe', 'ingredient')
    list_filter = ('recipe', 'ingredient')
    search_fields = ('recipe', 'ingredient')


admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(IngredientAmount, IngredientAmountAdmin)
admin.site.register(IngredientRecipe, IngredientRecipeAdmin)
admin.site.register(FavoritesRecipes)
admin.site.register(ShoppingCart)
