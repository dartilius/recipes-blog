from django.shortcuts import get_object_or_404
from rest_framework import serializers

from recipes.models import Recipe
from users.models import User


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
            'is_subscribed',
        )
        read_only_fields = ('is_subscribed',)
        model = User

    def get_is_subscribed(self, obj):
        if not self.context.get('request').user.is_authenticated:
            return False
        return obj.following.filter(
            user=self.context.get('request').user
        ).exists()


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
        model = User
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_username(self, value):
        if value == 'me':
            raise serializers.ValidationError(
                "Недопустимый username."
            )
        return value

    def create(self, data):
        user = User.objects.create(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name']
        )
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
    recipes_count = serializers.SerializerMethodField(read_only=True)
    is_subscribed = serializers.SerializerMethodField()

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
        read_only_fields = ('is_subscribed', 'recipes', 'recipes_count')
        model = User

    def get_is_subscribed(self, obj):
        if not self.context.get('request').user.is_authenticated:
            return False
        return obj.following.filter(
            user=self.context.get('request').user
        ).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        recipes_limit = self.context.get(
            'request'
        ).query_params.get('recipes_limit')
        if recipes_limit:
            recipes = obj.recipes.all().order_by(
                '-pub_date'
            )[:int(recipes_limit)]
        else:
            recipes = obj.recipes.all().order_by('-pub_date')
        serializer = RecipeUserSerializer(instance=recipes, many=True)
        return serializer.data
