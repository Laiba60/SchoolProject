from results.models import Result


def test_student_downloads_own_pdf_only(as_user, anon, student_a, student_b):
    Result.objects.create(student=student_a, subject="english", total_marks=100, obtained_marks=88)
    c = as_user(student_a)
    r = c.get("/api/reports/student/S-1/pdf/?dl=1")
    assert r.status_code == 200 and r.content[:4] == b"%PDF" and "attachment" in r["Content-Disposition"]
    assert c.get("/api/reports/student/S-2/pdf/").status_code == 403
    assert anon.get("/api/reports/student/S-1/pdf/").status_code in (401, 403)


def test_admin_downloads_any_pdf_and_teacher_cannot(as_user, admin, teacher, student_b):
    assert as_user(admin).get("/api/reports/student/S-2/pdf/").content[:4] == b"%PDF"
    assert as_user(admin).get("/api/reports/student/nobody/pdf/").status_code == 404
    assert as_user(teacher).get("/api/reports/student/S-2/pdf/").status_code == 403


def test_pdf_handles_markup_in_names(as_user, admin, student_a):
    student_a.full_name = "<b>Evil & Co</b>"
    student_a.save()
    assert as_user(admin).get("/api/reports/student/S-1/pdf/").status_code == 200
