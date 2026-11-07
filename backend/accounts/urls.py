from django.urls import path

from . import views

urlpatterns = [
    path("auth/csrf/", views.CsrfView.as_view()),
    path("auth/login/", views.LoginView.as_view()),
    path("auth/logout/", views.LogoutView.as_view()),
    path("auth/me/", views.MeView.as_view()),
    path("auth/register/", views.RegisterView.as_view()),
    path("users/public/", views.PublicUsersView.as_view()),
    path("admin/users/", views.AdminUsersView.as_view()),
    path("admin/users/<int:pk>/", views.AdminUserDetailView.as_view()),
    path("admin/users/<int:pk>/<str:action>/", views.AdminUserDetailView.as_view()),
]
