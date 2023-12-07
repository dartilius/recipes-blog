from django.contrib.auth.tokens import default_token_generator
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status, mixins
from rest_framework.decorators import action, api_view
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from users.models import User
from users.serializers import UserSerializer, TokenSerializer, ChangePasswordSerializer, FollowSerializer


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет пользователей."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageNumberPagination

    def perform_create(self, serializer):
        serializer.is_valid(raise_exception=True)
        serializer.save(data=self.request.data)
        user = User.objects.get(username=self.request.data['username'])
        user.set_password(self.request.data['password'])

    @action(
        ['GET'],
        url_path='me',
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def get_data_me(self, request):
        serializer = UserSerializer(
            request.user
        )
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
    @action(
        ['POST'],
        url_path='set_password',
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(request.data['current_password']):
            return Response(
                'Неверный пароль.',
                status=HTTP_400_BAD_REQUEST
            )
        request.user.set_password(request.data['new_password'])
        request.user.save()
        return Response('Пароль успешно изменен.', status=HTTP_204_NO_CONTENT)


@api_view(['POST'])
def get_token(request):
    """Получение токена авторизации."""
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = request.data.get('email')
    user = get_object_or_404(User, email=email)
    return Response(
        {'auth_token': str(AccessToken.for_user(user))},
        status=status.HTTP_201_CREATED
    )


@api_view
def logout(request):
    if not request.user.is_authenticated:
        return Response(status=HTTP_401_UNAUTHORIZED)
    AccessToken.for_user(request.user).delete()
    return Response(status=HTTP_204_NO_CONTENT)


class FollowViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """Вьюсет для модели Follow."""

    serializer_class = FollowSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ('following__username', 'user__username')

    def get_queryset(self):
        return self.request.user.follower.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
