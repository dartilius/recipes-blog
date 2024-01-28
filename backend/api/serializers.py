from recipes.models import (FavoriteRecipe, Ingredient, IngredientAmount,
                            Recipe, ShoppingCart, Tag)
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from users.models import User


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

    id = serializers.IntegerField()

    class Meta:
        model = IngredientAmount
        fields = (
            'id',
            'amount'
        )

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


class UserSerializer(serializers.ModelSerializer):
    """Сериалайзер пользоватлея."""

    is_subscribed = serializers.BooleanField(read_only=True)

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )
        model = User


class TagPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
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
    tags = TagPrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True,
        allow_empty=False
    )
    ingredients = IngredientAmountSerializer(
        many=True,
        required=True,
        allow_empty=False
    )
    image = Base64ImageField()
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

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
        read_only_fields = ('id', 'author', 'is_favorited', 'is_in_shopping_cart')
        model = Recipe

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
        super(self.__class__, self).update(instance, validated_data)
        instance.save()
        return instance

    # def validate_ingredients(self, value):
    #     keys = [sub['id'] for sub in value]
    #     if len(set(keys)) != len(keys):
    #         raise serializers.ValidationError(
    #             'Повторяющиеся ингредиенты.'
    #         )
    #     return value


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
        fields = ('user', 'recipe')
        read_only_fields = ('user', 'recipe')


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
        model = FavoriteRecipe
        fields = ('user', 'recipe')
        read_only_fields = ('user', 'recipe')

    def validate(self, data):
        request = self.context.get('request')
        user = request.user
        recipe_id = self.context.get('view').kwargs.get('recipe_id')
        recipe = get_object_or_404(id=recipe_id)
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


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериалайзер пользоватлея."""

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        )
        read_only_fields = ('id',)
        model = User
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_username(self, value):
        if value == 'me':
            raise serializers.ValidationError(
                'Недопустимый username.'
            )
        return value

    def create(self, data):
        user = super(self.__class__, self).create(data)
        user.set_password(data['password'])
        user.save()
        return user


class TokenSerializer(serializers.Serializer):
    """Сериалайзер для получения токена."""

    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(max_length=150)

    def validate(self, data):
        user = get_object_or_404(User, email=data['email'])
        if not user.check_password(data['password']):
            raise serializers.ValidationError(
                'Неверный пароль!'
            )
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """Сериалайзер для смены пароля пользователя."""

    new_password = serializers.CharField(max_length=150)
    current_password = serializers.CharField(max_length=150)


class RecipeUserSerializer(serializers.ModelSerializer):
    """Рецепты в подписках."""

    class Meta:
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        model = Recipe


class SubscriptionsSerializer(serializers.ModelSerializer):
    """Сериалайзер для подписок."""

    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.IntegerField(read_only=True)
    is_subscribed = serializers.BooleanField(read_only=True)

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )
        model = User

    def get_recipes(self, obj):
        recipes_limit = self.context.get(
            'request'
        ).query_params.get('recipes_limit')
        recipes = obj.recipes.order_by('-pub_date')
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        serializer = RecipeUserSerializer(instance=recipes, many=True)
        return serializer.data
