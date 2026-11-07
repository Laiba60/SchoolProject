from django.urls import path

from .views import StudentPdfView

urlpatterns = [path("reports/student/<str:uid>/pdf/", StudentPdfView.as_view())]
