from django.contrib.auth import login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .backends import UidBackend
from .models import Role, Status, User
from .permissions import IsAdminRole
from .serializers import AdminUserSerializer, PublicUserSerializer, RegisterSerializer, UserSerializer

BAD_LOGIN = "Invalid ID or password."


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    """GET sets the csrftoken cookie that the React app echoes in X-CSRFToken."""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"detail": "ok"})


# csrf_protect: login and register are also checked for a CSRF token, not only logged-in requests.
@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        uid = str(request.data.get("uid", "")).strip()
        password = str(request.data.get("password", ""))
        role = request.data.get("role")
        user = UidBackend().check_credentials(uid, password)
        # A wrong role gets the same message as a wrong password (no account probing).
        if user is None or (role and user.role != role):
            return Response({"detail": BAD_LOGIN}, status=status.HTTP_400_BAD_REQUEST)
        if user.status == Status.PENDING:
            return Response({"detail": "Your account is still waiting for Admin approval."}, status=403)
        if user.status == Status.BLOCKED or not user.is_active:
            return Response({"detail": "Your account has been blocked. Contact the Admin."}, status=403)
        login(request._request, user, backend="accounts.backends.UidBackend")
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logout(request._request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


@method_decorator(csrf_protect, name="dispatch")
class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response({"detail": "Registration submitted. Waiting for Admin approval.", "uid": user.uid},
                        status=status.HTTP_201_CREATED)


def _non_admins():
    return User.objects.exclude(role=Role.ADMIN).select_related("section").prefetch_related("sections")


@method_decorator(never_cache, name="dispatch")
class PublicUsersView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = PublicUserSerializer

    def get_queryset(self):
        return _non_admins().order_by("-created_at", "-id")


class AdminUsersView(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminUserSerializer

    def get_queryset(self):
        qs, p = _non_admins().order_by("-created_at", "-id"), self.request.query_params
        if p.get("role") in (Role.TEACHER, Role.STUDENT):
            qs = qs.filter(role=p["role"])
        if p.get("status") in Status.values:
            qs = qs.filter(status=p["status"])
        if p.get("search"):
            from django.db.models import Q
            qs = qs.filter(Q(uid__icontains=p["search"]) | Q(full_name__icontains=p["search"]))
        return qs


ACTIONS = {"approve": Status.APPROVED, "block": Status.BLOCKED, "unblock": Status.APPROVED}


class AdminUserDetailView(APIView):
    permission_classes = [IsAdminRole]

    def _user(self, pk):
        return generics.get_object_or_404(User.objects.exclude(role=Role.ADMIN), pk=pk)

    def delete(self, request, pk):
        self._user(pk).delete()  # a student's results go too; a teacher's results are kept
        return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, pk, action):
        if action not in ACTIONS:
            return Response({"detail": "Unknown action."}, status=status.HTTP_400_BAD_REQUEST)
        user = self._user(pk)
        user.status = ACTIONS[action]
        user.save(update_fields=["status"])
        return Response(AdminUserSerializer(user).data)
