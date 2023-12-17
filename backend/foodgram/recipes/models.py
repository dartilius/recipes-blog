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

    def __str__(self):
        return self.name


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

    def __str__(self):
        return self.name


class IngredientAmount(models.Model):
    """Ингредиенты в рецепте."""

    ingredient_amount_pk = models.AutoField(primary_key=True)
    amount = models.PositiveIntegerField(
        verbose_name='Количество'
    )
    id = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='ingredients_amount'
    )


class Recipe(models.Model):
    """Рецепт."""

    author = models.ForeignKey(
        User,
        related_name='recipes',
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
        upload_to='recipes/images/',
        blank=True
    )
    tags = models.ManyToManyField(Tag)
    ingredients = models.ManyToManyField(IngredientAmount)
    is_favorited = models.ManyToManyField(
        User,
        through='FavoritesRecipes',
        related_name='recipes_is_favorited'
    )
    is_in_shopping_cart = models.ManyToManyField(
        User,
        through='ShoppingCart',
        related_name='recipes_is_in_shopping_cart'
    )
    pub_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


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
