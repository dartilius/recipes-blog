from django.contrib import admin

from recipes.models import Tag, Recipe, Ingredient


class TagAdmin(admin.ModelAdmin):
    """Тег."""

    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name', 'slug')


class RecipeAdmin(admin.ModelAdmin):
    """Рецепт."""

    list_display = ('author', 'name', 'text', 'cooking_time')
    list_filter = ('author', 'name', 'text', 'cooking_time')
    search_fields = ('author', 'name', 'text', 'cooking_time')


class IngredientAdmin(admin.ModelAdmin):
    """Ингредиент."""

    list_display = ('name', 'measurement_unit')
    list_filter = ('name', 'measurement_unit')
    search_fields = ('name', 'measurement_unit')


class RecipeTagAdmin(admin.ModelAdmin):
    """Теги рецептов."""

    list_display = ('recipe', 'tag')
    list_filter = ('recipe', 'tag')
    search_fields = ('recipe', 'tag')

class RecipeIngredientAdmin(admin.ModelAdmin):
    """Ингредиенты рецептов."""

    list_display = ('recipe', 'ingredient')
    list_filter = ('recipe', 'ingredient')
    search_fields = ('recipe', 'ingredient')


admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
# admin.site.register(RecipeTag, RecipeTagAdmin)
# admin.site.register(RecipeIngredient, RecipeIngredientAdmin)
