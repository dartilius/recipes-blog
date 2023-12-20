from rest_framework import serializers

from recipes.models import (FavoritesRecipes, Ingredient, IngredientAmount,
                            Recipe, ShoppingCart, Tag)
from users.models import User
from users.serializers import UserSerializer


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


class IngredientAmountSerializer(serializers.ModelSerializer):
    """Сериалайзер для добавления ингредиентов в рецепт."""

    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = ('name', 'measurement_unit')

    def get_name(self, obj):
        return obj.id.name

    def get_measurement_unit(self, obj):
        return obj.id.measurement_unit

    def validate(self, data):
        if data['amount'] <= 0:
            raise serializers.ValidationError(
                'Ингредиентов должно быть больше 0.'
            )
        return data


class Base64ImageField(serializers.ImageField):
    """Отображение картинок."""

    def to_internal_value(self, data):
        import base64
        import uuid

        import six
        from django.core.files.base import ContentFile

        if isinstance(data, six.string_types):
            if 'data:' in data and ';base64,' in data:
                header, data = data.split(';base64,')

            try:
                decoded_file = base64.b64decode(data)
            except TypeError:
                self.fail('invalid_image')

            file_name = str(uuid.uuid4())[:12]
            file_extension = self.get_file_extension(file_name, decoded_file)
            complete_file_name = "%s.%s" % (file_name, file_extension, )
            data = ContentFile(decoded_file, name=complete_file_name)

        return super(Base64ImageField, self).to_internal_value(data)

    def get_file_extension(self, file_name, decoded_file):
        import imghdr

        extension = imghdr.what(file_name, decoded_file)
        extension = "jpg" if extension == "jpeg" else extension

        return extension


class ObjectPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """Отображение полей Тега."""

    def to_representation(self, value):
        return {
            'id': value.id,
            'name': value.name,
            'color': value.color,
            'slug': value.slug
        }


class RecipeSerializer(serializers.ModelSerializer):
    """Сериалайзер для модели Recipe."""

    author = UserSerializer(read_only=True)
    tags = ObjectPrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        required=True,
        allow_empty=False
    )
    ingredients = IngredientAmountSerializer(
        many=True,
        required=True,
        allow_empty=False
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )
        read_only_fields = ('author', 'is_favorited', 'is_in_shopping_cart')
        model = Recipe

    def get_tags(self, value):
        return TagSerializer(Tag.objects.get(id=value))

    def validate_cooking_time(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Время приготовления должно быть больше 0.'
            )
        return value

    def validate_tags(self, value):
        if not len(set(value)) == len(value):
            raise serializers.ValidationError('Повторяющиеся теги.')
        return value

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance = Recipe.objects.create(**validated_data)
        instance.tags.set(tags)
        ingredients_ids = []
        for ingredient in ingredients:
            ingredients_ids.append(
                IngredientAmount.objects.get_or_create(
                    **ingredient
                )[0].pk
            )
        instance.ingredients.set(ingredients_ids)
        return instance

    def update(self, instance, validated_data):
        if 'ingredients' not in validated_data:
            raise serializers.ValidationError('Не добавлены ингредиенты.')
        if 'tags' not in validated_data:
            raise serializers.ValidationError('Не добавлены теги.')
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.set(tags)
        ingredients_ids = []
        for ingredient in ingredients:
            ingredients_ids.append(
                IngredientAmount.objects.get_or_create(
                    **ingredient
                )[0].pk
            )
        instance.ingredients.set(ingredients_ids)
        instance.image = validated_data['image']
        instance.save()
        return instance

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

    def validate_ingredients(self, value):
        keys = [sub['id'] for sub in value]
        if len(set(keys)) != len(keys):
            raise serializers.ValidationError(
                'Повторяющиеся ингредиенты.'
            )
        return value


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериалайзер для списка покупок."""

    user = serializers.SlugRelatedField(
        default=serializers.CurrentUserDefault(),
        queryset=User.objects.all(),
        slug_field='username'
    )

    def to_representation(self, value):
        return {
            'id': value.recipe.id,
            'name': value.recipe.name,
            'image': self.context.get('request').build_absolute_uri(
                value.recipe.image.url
            ),
            'cooking_time': value.recipe.cooking_time
        }

    class Meta:
        model = ShoppingCart
        read_only_fields = ('user', 'recipe')
        exclude = ('recipe',)

    def validate(self, data):
        request = self.context.get('request')
        user = request.user
        recipe_id = self.context.get('view').kwargs.get('recipe_id')
        if not Recipe.objects.filter(id=recipe_id).exists():
            raise serializers.ValidationError('Такого рецепта не существует.')
        recipe = Recipe.objects.get(id=recipe_id)
        if request.method == 'POST':
            if recipe.shopping_carts.filter(user=user, recipe=recipe):
                raise serializers.ValidationError(
                    'Рецепт уже добавлен в список покупок.'
                )
        if request.method == 'DELETE':
            if not recipe.shopping_carts.filter(user=user, recipe=recipe):
                raise serializers.ValidationError(
                    'Рецепта нет в списке покупок.'
                )
        return data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериалайзер для списка покупок."""

    user = serializers.SlugRelatedField(
        default=serializers.CurrentUserDefault(),
        queryset=User.objects.all(),
        slug_field='username'
    )

    def to_representation(self, value):
        return {
            'id': value.recipe.id,
            'name': value.recipe.name,
            'image': self.context.get('request').build_absolute_uri(
                value.recipe.image.url
            ),
            'cooking_time': value.recipe.cooking_time
        }

    class Meta:
        model = FavoritesRecipes
        read_only_fields = ('user', 'recipe')
        exclude = ('recipe',)

    def validate(self, data):
        request = self.context.get('request')
        user = request.user
        recipe_id = self.context.get('view').kwargs.get('recipe_id')
        if not Recipe.objects.filter(id=recipe_id).exists():
            raise serializers.ValidationError('Такого рецепта не существует.')
        recipe = Recipe.objects.get(id=recipe_id)
        if request.method == 'POST':
            if recipe.favorite_recipes.filter(user=user, recipe=recipe):
                raise serializers.ValidationError(
                    'Рецепт уже добавлен в избранное.'
                )
        if request.method == 'DELETE':
            if not recipe.favorite_recipes.filter(user=user, recipe=recipe):
                raise serializers.ValidationError(
                    'Рецепта нет в избранном.'
                )
        return data
