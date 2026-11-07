import pytest
from django.db import IntegrityError, transaction

from accounts.models import Role, Status, User
from school.models import Section
from results.grading import grade_for
from results.models import Result


@pytest.mark.parametrize("pct,expected", [
    (100, "A+"), (90, "A+"), (89.99, "A"), (80, "A"), (79.99, "B"), (70, "B"),
    (69.99, "C"), (60, "C"), (59.99, "D"), (50, "D"), (49.99, "F"), (0, "F"),
])
def test_grade_boundaries(pct, expected):
    assert grade_for(pct) == expected


@pytest.fixture
def student(db):
    sec = Section.objects.create(class_name="9th", section="A")
    return User.objects.create_user("S1", "pass12345", role=Role.STUDENT, full_name="S", section=sec,
                                    status=Status.APPROVED)


@pytest.mark.parametrize("total,obtained", [(0, 0), (100, 101)])
def test_result_check_constraint(student, total, obtained):
    with pytest.raises(IntegrityError), transaction.atomic():
        Result.objects.create(student=student, subject="Math", total_marks=total, obtained_marks=obtained)


def test_result_unique_per_student_subject_normalized(student):
    Result.objects.create(student=student, subject="Math ", total_marks=100, obtained_marks=50)
    with pytest.raises(IntegrityError), transaction.atomic():
        Result.objects.create(student=student, subject="  MATH", total_marks=100, obtained_marks=60)


def test_uid_unique_case_insensitive(student):
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user("s1", "pass12345", role=Role.STUDENT, full_name="X")
