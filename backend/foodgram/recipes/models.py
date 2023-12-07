from django.db import models
from colorfield.fields import ColorField

from users.models import User


class Tag(models.Model):
    """Тег."""

    name = models.CharField(
        max_length=200,
        verbose_name='Название',
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Слаг',
        max_length=200,
    )
    color = ColorField(
        blank=True,
        null=True
    )


class Ingredient(models.Model):
    """Ингредиент."""

    name = models.CharField(
        verbose_name='Ингредиент',
        max_length=200
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=200
    )


class Recipe(models.Model):
    """Рецепт."""

    author = models.ForeignKey(
        User,
        related_name='author',
        on_delete=models.CASCADE
    )
    name = models.TextField(
        verbose_name='Название'
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    cooking_time = models.PositiveIntegerField()
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='recipes/',
        blank=True
    )
    tags = models.ManyToManyField(Tag)
    ingredients = models.ManyToManyField(Ingredient)


class IngredientAmount(models.Model):
    """Ингредиенты в рецепте."""

    amount = models.PositiveIntegerField(
        verbose_name='Количество'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='ingredients_amount'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipe_amount'
    )


class FavoritesRecipes(models.Model):
    """Избранные рецепты."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Избранное',
        related_name='favorite_recipes'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorite_recipes'
    )

class ShoppingCart(models.Model):
    """Список покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='shopping_carts'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Покупка',
        related_name='shopping_carts'
    )
