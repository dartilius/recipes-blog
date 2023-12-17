from rest_framework import permissions


class IsAuthor(permissions.BasePermission):
    """Права доступа для автора."""

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_authenticated and
            request.method in permissions.SAFE_METHODS
            or (
                request.user == obj.author
            )
        )
