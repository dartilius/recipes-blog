from django.shortcuts import get_object_or_404
from rest_framework import serializers

from users.models import User, Follow


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
        read_only_fields = ('is_subscribed', 'id')
        model = User


    def get_is_subscribed(self, obj):
        return True

    def validate_username(self, value):
        if value == 'me':
            raise serializers.ValidationError(
                "Недопустимый username."
            )
        return value


    def create(self, data):
        User.objects.create(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name']
        )
        return data


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


class FollowSerializer(serializers.ModelSerializer):
    """Сериалайзер для подписок."""

    user = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username',
        default=serializers.CurrentUserDefault()
    )
    following = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field='username',
        read_only=False
    )

    class Meta:
        fields = ('user', 'following')
        model = Follow
        validators = (
            serializers.UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'following'),
                message='Нельзя подписаться дважды!'
            ),
        )

    def validate(self, attrs):
        if self.context['request'].user == attrs['following']:
            raise serializers.ValidationError('Нельзя подписаться на себя!')
        return attrs
