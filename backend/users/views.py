from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (HTTP_200_OK, HTTP_201_CREATED,
                                   HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST,
                                   HTTP_401_UNAUTHORIZED)

from api.filters import UserFilter
from api.paginations import PageLimitPagination
from api.tokens import CustomAccessToken
from users.models import Follow, User
from users.serializers import (ChangePasswordSerializer,
                               SubscriptionsSerializer, TokenSerializer,
                               UserCreateSerializer, UserSerializer)


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет пользователей."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageLimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = UserFilter

    def perform_create(self, serializer):
        serializer.is_valid(raise_exception=True)
        if 'password' not in self.request.data:
            return Response(status=HTTP_400_BAD_REQUEST)
        else:
            serializer.save(data=self.request.data)
            user = User.objects.get(username=self.request.data['username'])
            user.set_password(self.request.data['password'])
            user.save()
            return Response(serializer.data, status=HTTP_201_CREATED)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        else:
            return UserSerializer

    @action(
        ['GET'],
        url_path='me',
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def get_data_me(self, request):
        serializer = UserSerializer(
            request.user,
            context={'request': request}
        )
        return Response(
            serializer.data,
            status=HTTP_200_OK
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

    @action(
        ['POST', 'DELETE'],
        detail=True,
        permission_classes=(IsAuthenticated,),
        url_path='subscribe'
    )
    def subscribe(self, request, pk):
        if request.method == 'POST':
            user = get_object_or_404(User, id=pk)
            serializer = SubscriptionsSerializer(
                user,
                context={'request': request}
            )
            if request.user == user:
                return Response(
                    "нельзя подписаться на себя.",
                    status=HTTP_400_BAD_REQUEST
                )
            if not Follow.objects.filter(user=request.user, following=user):
                Follow.objects.create(
                    user=request.user,
                    following=user
                )
                return Response(serializer.data, status=HTTP_201_CREATED)
            return Response("Вы уже подписаны.", status=HTTP_400_BAD_REQUEST)
        if request.method == 'DELETE':
            if not Follow.objects.filter(
                user=request.user,
                following=get_object_or_404(User, id=pk)
            ).exists():
                return Response(status=HTTP_400_BAD_REQUEST)
            Follow.objects.filter(
                user=request.user,
                following=User.objects.get(id=pk)
            ).delete()
            return Response(status=HTTP_204_NO_CONTENT)
        return Response(status=HTTP_400_BAD_REQUEST)

    @action(
        ['GET',],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions'
    )
    def get_subscriptions(self, request):
        queryset = User.objects.filter(
            following__user=request.user
        ).order_by('id')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscriptionsSerializer(
                page,
                context={'request': request},
                many=True
            )
            return self.get_paginated_response(
                data=serializer.data
            )
        serializer = SubscriptionsSerializer(
            queryset,
            context={'request': request},
            many=True
        )
        return Response(serializer.data)


@api_view(['POST'])
def get_token(request):
    """Получение токена авторизации."""
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = request.data.get('email')
    user = get_object_or_404(User, email=email)
    return Response(
        {'auth_token': str(CustomAccessToken.for_user(user))},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
def logout(request):
    """Выход из системы."""
    if not request.user.is_authenticated:
        return Response(status=HTTP_401_UNAUTHORIZED)
    request.auth.blacklist()
    return Response(status=HTTP_204_NO_CONTENT)
