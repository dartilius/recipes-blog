from django.urls import path, include
from rest_framework.authtoken import views
from rest_framework.routers import SimpleRouter

from users.views import UserViewSet, get_token, logout
from .views import TagViewSet, RecipeViewSet, IngredientViewSet, ShoppingCartViewSet

router = SimpleRouter()

router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('users', UserViewSet, basename='users')
router.register('ingredients', IngredientViewSet, basename='ingredients')
# router.register(
#     r'recipes/(?P<recipe_id>\d+)/shopping_cart',
#     ShoppingCartViewSet,
#     basename='shopping_cart'
# )

urlpatterns = [
    path('', include(router.urls)),
    path(
        'auth/token/login/',
        get_token,
        name='token_obtain_pair'
    ),
    path('auth/token/logout/', logout, name='logout')
    #path('api/users/', signup, name='signup')
    # path('v1/api-token-auth/', views.obtain_auth_token)
]