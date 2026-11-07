import io

import pytest
from openpyxl import Workbook

from accounts.models import Role
from conftest import make
from results.models import Result


def sheet(rows, header=("Student Name", "Roll No", "Total Marks", "Obtained Marks")):
    wb = Workbook()
    ws = wb.active
    ws.append(list(header))
    for r in rows:
        ws.append(list(r))
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    buf.name = "r.xlsx"
    return buf


def add(c, uid, total=100, got=80):
    return c.post("/api/teacher/results/", {"student_uid": uid, "total_marks": total, "obtained_marks": got}, format="json")


# ---- teacher: manual entry, permissions -----------------------------------------
def test_teacher_saves_updates_and_deletes_own_subject_result(as_user, teacher, student_a):
    t = as_user(teacher)
    r = add(t, "S-1")
    assert r.status_code == 201 and r.json()["subject"] == "English" and r.json()["grade"] == "A"
    assert add(t, "s-1", 100, 95).status_code == 201  # same student+subject updates, not duplicates
    assert Result.objects.count() == 1 and Result.objects.get().obtained_marks == 95
    rid = Result.objects.get().pk
    assert t.put(f"/api/teacher/results/{rid}/", {"total_marks": 50, "obtained_marks": 10}, format="json").json()["percentage"] == 20.0
    assert t.delete(f"/api/teacher/results/{rid}/").status_code == 204


def test_teacher_cannot_touch_other_sections(as_user, teacher, teacher2, student_a, student_b):
    assert add(as_user(teacher), "S-2").status_code == 400  # S-2 is in 9th-B
    add(as_user(teacher2), "S-2")
    rid = Result.objects.get().pk
    t = as_user(teacher)
    assert t.put(f"/api/teacher/results/{rid}/", {"total_marks": 10, "obtained_marks": 1}, format="json").status_code == 404
    assert t.delete(f"/api/teacher/results/{rid}/").status_code == 404
    assert t.get("/api/teacher/results/").json()["count"] == 0
    assert [s["uid"] for s in t.get("/api/teacher/students/").json()] == ["S-1"]


@pytest.mark.parametrize("total,got", [(0, 0), (100, 101), (100, -1), ("x", 1), (50.5, 10)])
def test_teacher_marks_validation(as_user, teacher, student_a, total, got):
    assert add(as_user(teacher), "S-1", total, got).status_code == 400


def test_pending_students_are_not_listed_or_accepted(as_user, teacher, sec_a):
    from accounts.models import Status
    make("S-P", Role.STUDENT, section=sec_a, status=Status.PENDING)
    t = as_user(teacher)
    assert t.get("/api/teacher/students/").json() == []
    assert add(t, "S-P").status_code == 400


def test_students_and_teachers_cannot_use_each_others_endpoints(as_user, anon, teacher, student_a):
    for url in ("/api/teacher/students/", "/api/teacher/analytics/", "/api/teacher/results/"):
        assert as_user(student_a).get(url).status_code == 403
        assert anon.get(url).status_code in (401, 403)
    assert as_user(teacher).get("/api/student/me/").status_code == 403
    assert as_user(teacher).get("/api/admin/results/").status_code == 403


# ---- analytics ------------------------------------------------------------------------
def test_analytics_numbers(as_user, teacher, sec_a, sec_b):
    s = [make(f"S{i}", Role.STUDENT, section=sec_a, father_name="d") for i in range(4)]
    t = as_user(teacher)
    for st, got in zip(s, (95, 85, 75, 40)):  # A+, A, B, F
        add(t, st.uid, 100, got)
    d = t.get("/api/teacher/analytics/").json()
    assert d["count"] == 4 and d["average"] == 73.75
    assert d["grade_distribution"] == {"A+": 1, "A": 1, "B": 1, "C": 0, "D": 0, "F": 1}
    assert d["section_averages"] == [{"section": "9th-A", "average": 73.75}]


def test_analytics_empty(as_user, teacher):
    d = as_user(teacher).get("/api/teacher/analytics/").json()
    assert d["count"] == 0 and d["average"] is None


def test_analytics_only_counts_own_subject_and_sections(as_user, teacher, teacher2, student_a, student_b):
    add(as_user(teacher), "S-1", 100, 50)
    add(as_user(teacher2), "S-2", 100, 100)
    Result.objects.create(student=student_a, subject="Math", total_marks=10, obtained_marks=10)  # other subject
    assert as_user(teacher).get("/api/teacher/analytics/").json()["average"] == 50.0


# ---- excel ------------------------------------------------------------------------------
def test_excel_template_downloads(as_user, teacher):
    r = as_user(teacher).get("/api/teacher/results/template/")
    assert r.status_code == 200 and b"".join(r.streaming_content)[:2] == b"PK"


def test_excel_import_edge_cases(as_user, teacher, student_a, student_b, sec_a):
    make("201", Role.STUDENT, section=sec_a, father_name="d")  # numeric roll no
    f = sheet([
        ("A", "S-1", 100, 90),          # ok
        ("B", 201.0, 50, 25),           # numeric cell 201.0 matches "201"
        ("C", " s-3 ", 100, 10),        # unknown student
        ("D", "S-2", 100, 10),          # exists but other section
        ("E", "S-1", 100, 120),         # obtained > total
        ("F", "S-1", "abc", 5),         # not a number
        ("G", "S-1", 100.5, 5),         # not whole
        (None, None, None, None),       # blank row skipped
        ("H", "", 100, 5),              # empty roll
    ])
    r = as_user(teacher).post("/api/teacher/results/import/", {"file": f}, format="multipart")
    assert r.status_code == 200
    body = r.json()
    assert body["imported"] == 2 and len(body["errors"]) == 6
    assert {e["row"] for e in body["errors"]} == {4, 5, 6, 7, 8, 10}
    assert Result.objects.count() == 2 and Result.objects.get(student__uid="201").obtained_marks == 25


def test_excel_import_rejects_bad_files(as_user, teacher):
    t = as_user(teacher)
    bad = io.BytesIO(b"not excel")
    bad.name = "x.xlsx"
    assert t.post("/api/teacher/results/import/", {"file": bad}, format="multipart").status_code == 400
    assert t.post("/api/teacher/results/import/", {"file": sheet([], header=("a", "b"))}, format="multipart").status_code == 400
    txt = io.BytesIO(b"x")
    txt.name = "x.csv"
    assert t.post("/api/teacher/results/import/", {"file": txt}, format="multipart").status_code == 400
    assert t.post("/api/teacher/results/import/", {}, format="multipart").status_code == 400


# ---- student ---------------------------------------------------------------------------------
def test_student_sees_only_own_results(as_user, teacher, teacher2, student_a, student_a2, student_b):
    add(as_user(teacher), "S-1", 100, 90)
    add(as_user(teacher), "S-3", 100, 10)
    Result.objects.create(student=student_a, subject="math", total_marks=100, obtained_marks=70)
    d = as_user(student_a).get("/api/student/me/").json()
    assert d["profile"]["uid"] == "S-1" and d["profile"]["section"] == "9th-A"
    assert [r["subject"] for r in d["results"]] == ["Math", "English"]  # 9th report-card order: Math comes before English
    assert d["total_marks"] == 200 and d["obtained_marks"] == 160 and d["percentage"] == 80.0 and d["grade"] == "A"
    assert "S-3" not in str(d)


def test_student_without_results(as_user, student_a):
    d = as_user(student_a).get("/api/student/me/").json()
    assert d["results"] == [] and d["grade"] == "-"


# ---- admin -----------------------------------------------------------------------------------
def test_admin_overview_and_result_management(as_user, admin, teacher, teacher2, student_a, student_b):
    add(as_user(teacher), "S-1", 100, 80)
    a = as_user(admin)
    ov = {o["teacher_uid"]: o for o in a.get("/api/admin/results/overview/").json()}
    assert ov["T-1"]["average"] == 80.0 and ov["T-1"]["count"] == 1 and ov["T-2"]["average"] is None
    r = a.post("/api/admin/results/", {"student_uid": "S-2", "subject": "Math", "total_marks": 50, "obtained_marks": 45}, format="json")
    assert r.status_code == 201 and r.json()["grade"] == "A+"
    rid = r.json()["id"]
    assert a.put(f"/api/admin/results/{rid}/", {"total_marks": 50, "obtained_marks": 20}, format="json").json()["grade"] == "F"
    assert a.get("/api/admin/results/?section=9th-B").json()["count"] == 1
    assert a.get("/api/admin/results/?subject=eng").json()["count"] == 1
    assert a.get("/api/admin/results/?teacher=ahmed").json()["count"] == 0
    assert a.get("/api/admin/results/?search=s-2").json()["count"] == 1
    assert a.post("/api/admin/results/", {"student_uid": "nobody", "subject": "x", "total_marks": 1, "obtained_marks": 1}, format="json").status_code == 400
    assert a.delete(f"/api/admin/results/{rid}/").status_code == 204
    # admin edits count in the teacher's analytics (same subject + sections)
    assert as_user(teacher).get("/api/teacher/analytics/").json()["count"] == 1


def test_deleting_student_removes_results_deleting_teacher_keeps_them(as_user, admin, teacher, student_a):
    add(as_user(teacher), "S-1")
    a = as_user(admin)
    a.delete(f"/api/admin/users/{teacher.pk}/")
    r = Result.objects.get()
    assert r.teacher is None
    a.delete(f"/api/admin/users/{student_a.pk}/")
    assert Result.objects.count() == 0
