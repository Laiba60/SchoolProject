"""Subjects must appear in the order of the printed Progress Report of the student's class."""
import io

import pytest
from openpyxl import load_workbook

from accounts.models import Role
from conftest import make
from results.models import Result
from school.models import Section
from school.subjects import group_for, subject_rank, term_for

JUNIOR = ["Urdu", "English", "Math", "Science", "Islamiyat", "History", "Geo", "Quran Translation", "Computer", "Drawing"]
SENIOR = ["Math", "Physics", "Chemistry", "Biology", "English", "Urdu", "Islamiyat", "Quran Translation", "Pakistan Studies"]


def fill(student, subjects):
    for s in reversed(subjects):  # insert backwards so the DB order is NOT the card order
        Result.objects.create(student=student, subject=s, total_marks=100, obtained_marks=70)


@pytest.mark.parametrize("name,group", [("6th", "junior"), ("8th", "junior"), ("Class 7", "junior"), ("9th", "senior"),
                                        ("10th", "senior"), ("5th", None), ("", None)])
def test_group_detection(name, group):
    assert group_for(name) == group


def test_term_label_only_for_9th_10th():
    assert term_for("9th") == "2nd Term" and term_for("10th") == "2nd Term" and term_for("7th") == ""


def test_spelling_variants_share_a_slot():
    assert subject_rank("maths", "9th") == subject_rank("Mathematics", "9th") == 0
    assert subject_rank("Computer", "9th") == subject_rank("biology", "9th") == 3
    assert subject_rank("Computer", "7th") == 8
    assert subject_rank("Astronomy", "9th") == 99


def test_student_page_order_for_class_8(as_user):
    sec = Section.objects.create(class_name="8th", section="A")
    st = make("S-8", Role.STUDENT, section=sec, father_name="D")
    fill(st, JUNIOR)
    rep = as_user(st).get("/api/student/me/").json()
    assert [r["subject"] for r in rep["results"]] == JUNIOR
    assert rep["profile"]["term"] == ""


def test_student_page_order_for_class_10_with_term_and_extras_last(as_user):
    sec = Section.objects.create(class_name="10th", section="A")
    st = make("S-10", Role.STUDENT, section=sec, father_name="D")
    fill(st, SENIOR + ["Zoology Extra", "Art Extra"])
    rep = as_user(st).get("/api/student/me/").json()
    assert [r["subject"] for r in rep["results"]] == SENIOR + ["Art Extra", "Zoology Extra"]
    assert rep["profile"]["term"] == "2nd Term"


def test_admin_list_uses_card_order(as_user, admin):
    s6 = Section.objects.create(class_name="6th", section="A")
    s9 = Section.objects.create(class_name="9th", section="A")
    a = make("S-6", Role.STUDENT, section=s6, father_name="D")
    b = make("S-9", Role.STUDENT, section=s9, father_name="D")
    fill(a, JUNIOR)
    fill(b, SENIOR)
    data = as_user(admin).get("/api/admin/results/?page_size=100").json()["results"]
    assert [r["subject"] for r in data if r["student_uid"] == "S-6"] == JUNIOR
    assert [r["subject"] for r in data if r["student_uid"] == "S-9"] == SENIOR


def test_subjects_endpoint_is_public(anon):
    d = anon.get("/api/subjects/").json()
    assert d["junior"]["subjects"] == JUNIOR[:7] + ["Quran Translation", "Computer", "Drawing"]
    assert d["senior"]["subjects"][3] == "Biology / Computer" and d["senior"]["term"] == "2nd Term"


def test_template_is_prefilled_with_teachers_students(as_user, teacher, student_a, student_a2):
    r = as_user(teacher).get("/api/teacher/results/template/")
    ws = load_workbook(io.BytesIO(b"".join(r.streaming_content))).active
    rows = list(ws.iter_rows(values_only=True))
    assert rows[0] == ("Student Name", "Roll No", "Class", "Total Marks", "Obtained Marks")
    assert [x[1] for x in rows[1:]] == ["S-1", "S-3"] and rows[1][2] == "9th-A"


def test_pdf_for_class_with_term_builds(as_user, admin):
    sec = Section.objects.create(class_name="9th", section="A")
    st = make("S-X", Role.STUDENT, section=sec, father_name="D")
    fill(st, SENIOR)
    assert as_user(admin).get("/api/reports/student/S-X/pdf/").content[:4] == b"%PDF"
