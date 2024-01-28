from django.contrib import admin

from .models import Follow, User

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Подписки."""

    list_display = ('following', 'user')
    list_filter = ('following__username', 'following__email', 'user')
    search_fields = ('following__username', 'following__email', 'user')



@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Пользователb."""

    list_display = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email', 'first_name', 'last_name')
