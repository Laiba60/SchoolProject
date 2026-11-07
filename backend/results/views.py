from django.db.models import Q
from django.http import FileResponse
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Role, Status, User
from accounts.permissions import IsAdminRole, IsStudent, IsTeacher
from school.models import Section
from school.subjects import rank_annotation, sequences

from . import excel
from .models import Result
from .serializers import ResultInputSerializer, ResultSerializer
from .services import results_qs, save_result, student_report, summarize, teacher_results, teacher_students


# ---------------------------------------------------------------- public
class SubjectSequencesView(APIView):
    """Subject order of the printed report card (6th-8th and 9th-10th); used for form suggestions."""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(sequences())


# ---------------------------------------------------------------- teacher
class TeacherStudentsView(APIView):
    permission_classes = [IsTeacher]

    def get(self, request):
        return Response([{"uid": s.uid, "full_name": s.full_name, "father_name": s.father_name,
                          "section": s.section.label} for s in teacher_students(request.user)])


class TeacherResultsView(generics.ListCreateAPIView):
    permission_classes = [IsTeacher]
    serializer_class = ResultSerializer

    def get_queryset(self):
        return teacher_results(self.request.user).order_by("student__section__class_name", "student__section__section", "student__uid")

    def create(self, request, *args, **kwargs):
        ser = ResultInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        student = teacher_students(request.user).filter(uid__iexact=d.get("student_uid", "").strip()).first()
        if not student:
            raise ValidationError({"student_uid": "No approved student with this roll no in your sections."})
        res = save_result(student, request.user.subject, d["total_marks"], d["obtained_marks"], teacher=request.user)
        return Response(ResultSerializer(results_qs().get(pk=res.pk)).data, status=status.HTTP_201_CREATED)


class TeacherResultDetailView(APIView):
    permission_classes = [IsTeacher]

    def _obj(self, request, pk):
        return generics.get_object_or_404(teacher_results(request.user), pk=pk)

    def put(self, request, pk):
        obj = self._obj(request, pk)
        ser = ResultInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        obj.total_marks, obj.obtained_marks, obj.teacher = ser.validated_data["total_marks"], ser.validated_data["obtained_marks"], request.user
        obj.save()
        return Response(ResultSerializer(obj).data)

    def delete(self, request, pk):
        self._obj(request, pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TeacherTemplateView(APIView):
    permission_classes = [IsTeacher]

    def get(self, request):
        return FileResponse(excel.build_template(request.user), as_attachment=True, filename="results_template.xlsx")


class TeacherImportView(APIView):
    permission_classes = [IsTeacher]
    parser_classes = [MultiPartParser]

    def post(self, request):
        f = request.FILES.get("file")
        if not f or not f.name.lower().endswith(".xlsx"):
            return Response({"detail": "Choose an .xlsx Excel file."}, status=400)
        if f.size > 5 * 1024 * 1024:
            return Response({"detail": "The file is larger than 5 MB."}, status=400)
        try:
            imported, errors = excel.import_results(request.user, f)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response({"imported": imported, "errors": errors})


class TeacherAnalyticsView(APIView):
    permission_classes = [IsTeacher]

    def get(self, request):
        return Response(summarize(teacher_results(request.user)))


# ---------------------------------------------------------------- student
class StudentMeView(APIView):
    permission_classes = [IsStudent]

    def get(self, request):
        return Response(student_report(request.user))


# ---------------------------------------------------------------- admin
class AdminOverviewView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        out = []
        teachers = User.objects.filter(role=Role.TEACHER).prefetch_related("sections").order_by("uid")
        for t in teachers:
            out.append({"teacher_uid": t.uid, "teacher_name": t.full_name, "subject": t.subject.title(),
                        **summarize(teacher_results(t))})
        return Response(out)  # not paginated: one card per teacher


class AdminResultsView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = ResultSerializer

    def get_queryset(self):
        qs = results_qs().annotate(subject_rank=rank_annotation()).order_by(
            "student__section__class_name", "student__section__section", "student__uid", "subject_rank", "subject")
        p = self.request.query_params
        if p.get("search"):
            qs = qs.filter(Q(student__uid__icontains=p["search"]) | Q(student__full_name__icontains=p["search"]))
        if p.get("section"):
            qs = qs.filter(student__section__in=[s.pk for s in Section.objects.all() if s.label == p["section"]])
        if p.get("subject"):
            qs = qs.filter(subject__icontains=p["subject"].strip().lower())
        if p.get("teacher"):
            qs = qs.filter(Q(teacher__uid__icontains=p["teacher"]) | Q(teacher__full_name__icontains=p["teacher"]))
        return qs

    def create(self, request, *args, **kwargs):
        ser = ResultInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        student = User.objects.filter(role=Role.STUDENT, uid__iexact=d.get("student_uid", "").strip()).first()
        if not student:
            raise ValidationError({"student_uid": "No student with this roll no."})
        if not d.get("subject", "").strip():
            raise ValidationError({"subject": "Enter the subject."})
        res = save_result(student, d["subject"], d["total_marks"], d["obtained_marks"])
        return Response(ResultSerializer(results_qs().get(pk=res.pk)).data, status=status.HTTP_201_CREATED)


class AdminResultDetailView(APIView):
    permission_classes = [IsAdminRole]

    def put(self, request, pk):
        obj = generics.get_object_or_404(Result, pk=pk)
        ser = ResultInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        obj.total_marks, obj.obtained_marks = ser.validated_data["total_marks"], ser.validated_data["obtained_marks"]
        obj.save()
        return Response(ResultSerializer(results_qs().get(pk=obj.pk)).data)

    def delete(self, request, pk):
        generics.get_object_or_404(Result, pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
