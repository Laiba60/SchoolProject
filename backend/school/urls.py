from django.urls import path

from . import views

urlpatterns = [
    path("sections/", views.SectionListView.as_view()),
    path("admin/sections/", views.SectionCreateView.as_view()),
    path("admin/sections/<int:pk>/", views.SectionDeleteView.as_view()),
    path("admin/branding/", views.BrandingView.as_view()),
]
