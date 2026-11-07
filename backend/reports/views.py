from django.http import HttpResponse
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.views import APIView

from accounts.models import Role, User

from .pdf import build_report


class StudentPdfView(APIView):
    """A student can download only his own report card; the admin can download any."""

    def get(self, request, uid):
        me = request.user
        if me.role == Role.STUDENT and me.uid.lower() != uid.lower():
            raise PermissionDenied("You can only download your own result.")
        if me.role not in (Role.STUDENT, Role.ADMIN):
            raise PermissionDenied("Not allowed.")
        student = User.objects.filter(role=Role.STUDENT, uid__iexact=uid).select_related("section").first()
        if not student:
            raise NotFound("No such student.")
        resp = HttpResponse(build_report(student), content_type="application/pdf")
        kind = "attachment" if request.query_params.get("dl") == "1" else "inline"
        resp["Content-Disposition"] = f'{kind}; filename="result_{student.uid}.pdf"'
        return resp
