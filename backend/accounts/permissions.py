from rest_framework.permissions import BasePermission

from .models import Role


class _HasRole(BasePermission):
    role = None

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.role == self.role)


class IsAdminRole(_HasRole):
    role = Role.ADMIN


class IsTeacher(_HasRole):
    role = Role.TEACHER


class IsStudent(_HasRole):
    role = Role.STUDENT
