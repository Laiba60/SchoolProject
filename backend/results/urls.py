from django.urls import path

from . import views as v

urlpatterns = [
    path("subjects/", v.SubjectSequencesView.as_view()),
    path("teacher/students/", v.TeacherStudentsView.as_view()),
    path("teacher/results/", v.TeacherResultsView.as_view()),
    path("teacher/results/template/", v.TeacherTemplateView.as_view()),
    path("teacher/results/import/", v.TeacherImportView.as_view()),
    path("teacher/results/<int:pk>/", v.TeacherResultDetailView.as_view()),
    path("teacher/analytics/", v.TeacherAnalyticsView.as_view()),
    path("student/me/", v.StudentMeView.as_view()),
    path("admin/results/overview/", v.AdminOverviewView.as_view()),
    path("admin/results/", v.AdminResultsView.as_view()),
    path("admin/results/<int:pk>/", v.AdminResultDetailView.as_view()),
]
