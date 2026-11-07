from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from .views import spa

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/", include("accounts.urls")),
    path("api/", include("school.urls")),
    path("api/", include("results.urls")),
    path("api/", include("reports.urls")),
    # Uploaded logo. Fine for one small file; use object storage / a CDN for anything bigger.
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    # Everything else is the React single-page app (client-side routing).
    re_path(r"^(?!api/|django-admin/|media/|static/)(?P<path>.*)$", spa),
]
