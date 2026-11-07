from django.conf import settings
from django.db import models
from django.db.models import F, Q

from school.utils import normalize_subject

from .grading import grade_for, percentage


class Result(models.Model):
    # Deleting a student removes his results; deleting a teacher keeps them (teacher -> NULL).
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="results",
        limit_choices_to={"role": "student"},
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="uploaded_results", limit_choices_to={"role": "teacher"},
    )
    subject = models.CharField(max_length=80)  # normalized in save()
    total_marks = models.PositiveIntegerField()
    obtained_marks = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["student__uid", "subject"]
        constraints = [
            models.UniqueConstraint(fields=["student", "subject"], name="result_unique_student_subject"),
            models.CheckConstraint(
                condition=Q(total_marks__gt=0) & Q(obtained_marks__gte=0) & Q(obtained_marks__lte=F("total_marks")),
                name="result_marks_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["subject"]),
            models.Index(fields=["teacher", "subject"]),
        ]

    def save(self, *args, **kwargs):
        self.subject = normalize_subject(self.subject)
        super().save(*args, **kwargs)

    @property
    def percentage(self):
        return percentage(self.obtained_marks, self.total_marks)

    @property
    def grade(self):
        return grade_for(self.percentage)

    def __str__(self):
        return f"{self.student_id}/{self.subject}: {self.obtained_marks}/{self.total_marks}"
