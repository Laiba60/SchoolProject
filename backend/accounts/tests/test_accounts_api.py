import pytest
from rest_framework.test import APIClient

from accounts.models import Role, Status, User
from conftest import PW, make


def teacher_payload(sec, **kw):
    d = dict(role="teacher", uid="T-100", full_name="Ahmed Ali", subject="English", mobile="03001234567",
             email="a@b.com", password=PW, confirm_password=PW, sections=[sec.pk])
    d.update(kw)
    return d


def student_payload(sec, **kw):
    d = dict(role="student", uid="S-200", full_name="Ali Ahmed", father_name="Ahmed", section=sec.pk, mobile="03001234567",
             email="a@b.com", password=PW, confirm_password=PW)
    d.update(kw)
    return d


# ---- registration -------------------------------------------------------------
def test_register_teacher_and_student_start_pending(anon, sec_a):
    assert anon.post("/api/auth/register/", teacher_payload(sec_a), format="json").status_code == 201
    assert anon.post("/api/auth/register/", student_payload(sec_a), format="json").status_code == 201
    t = User.objects.get(uid="T-100")
    assert t.status == Status.PENDING and t.subject == "english" and list(t.sections.all()) == [sec_a]
    assert User.objects.get(uid="S-200").section == sec_a
    assert t.password != PW  # hashed


@pytest.mark.parametrize("uid", ["t-100", "T-100", "admin", "ADMIN"])
def test_register_rejects_duplicate_and_reserved_ids(anon, sec_a, uid):
    make("T-100", Role.TEACHER, subject="x")
    r = anon.post("/api/auth/register/", student_payload(sec_a, uid=uid), format="json")
    assert r.status_code == 400 and "uid" in r.json()


@pytest.mark.parametrize("change,field", [
    ({"confirm_password": "other"}, "confirm_password"),
    ({"password": "short", "confirm_password": "short"}, "password"),
    ({"mobile": "abc"}, "mobile"), ({"email": "nope"}, "email"),
    ({"father_name": ""}, "father_name"), ({"section": None}, "section"),
])
def test_register_student_validation(anon, sec_a, change, field):
    r = anon.post("/api/auth/register/", student_payload(sec_a, **change), format="json")
    assert r.status_code == 400 and field in r.json()


def test_register_teacher_needs_subject_and_sections(anon, sec_a):
    r = anon.post("/api/auth/register/", teacher_payload(sec_a, subject="", sections=[]), format="json")
    assert {"subject", "sections"} <= set(r.json())


def test_register_and_login_enforce_csrf(sec_a):
    c = APIClient(enforce_csrf_checks=True)
    assert c.post("/api/auth/register/", student_payload(sec_a), format="json").status_code == 403
    assert c.post("/api/auth/login/", {"uid": "x", "password": "y"}, format="json").status_code == 403
    c.get("/api/auth/csrf/")
    token = c.cookies["csrftoken"].value
    r = c.post("/api/auth/register/", student_payload(sec_a), format="json", HTTP_X_CSRFTOKEN=token)
    assert r.status_code == 201


# ---- public live table -------------------------------------------------------------
def test_public_users_table_shows_no_secrets(anon, teacher, student_a, admin):
    data = anon.get("/api/users/public/").json()["results"]
    assert {u["uid"] for u in data} == {"T-1", "S-1"}  # admin hidden
    assert set(data[0]) == {"id", "role", "uid", "name", "info", "status"}
    blob = str(data)
    assert "t@x.com" not in blob and "0300111" not in blob and "pbkdf2" not in blob
    assert next(u for u in data if u["uid"] == "T-1")["info"] == "English (9th-A)"
    assert next(u for u in data if u["uid"] == "S-1")["info"] == "9th-A"


# ---- login ----------------------------------------------------------------------------
def test_login_ok_returns_user_and_session(anon, teacher):
    r = anon.post("/api/auth/login/", {"uid": "t-1", "password": PW, "role": "teacher"}, format="json")
    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "teacher" and body["subject"] == "English" and body["sections"] == ["9th-A"]
    assert anon.get("/api/auth/me/").json()["uid"] == "T-1"


def test_login_pending_blocked_wrong_password_and_wrong_role(anon, sec_a, student_a):
    make("P-1", Role.STUDENT, section=sec_a, status=Status.PENDING)
    make("B-1", Role.STUDENT, section=sec_a, status=Status.BLOCKED)
    post = lambda uid, pw=PW, role="student": anon.post("/api/auth/login/", {"uid": uid, "password": pw, "role": role}, format="json")
    assert post("P-1").status_code == 403 and "approval" in post("P-1").json()["detail"]
    assert post("B-1").status_code == 403 and "blocked" in post("B-1").json()["detail"]
    assert post("S-1", "wrong").status_code == 400
    assert post("S-1", role="teacher").status_code == 400  # student cannot use the teacher tab
    assert post("S-1", role="admin").status_code == 400
    # a wrong password never reveals the account status
    assert post("P-1", "wrong").status_code == 400


def test_login_is_throttled(anon, student_a):
    codes = [anon.post("/api/auth/login/", {"uid": "S-1", "password": "bad", "role": "student"}, format="json").status_code for _ in range(12)]
    assert codes[-1] == 429


def test_me_requires_login_and_logout_ends_session(anon, as_user, student_a):
    assert anon.get("/api/auth/me/").status_code in (401, 403)
    c = as_user(student_a)
    assert c.get("/api/auth/me/").status_code == 200
    assert c.post("/api/auth/logout/").status_code == 204
    assert c.get("/api/auth/me/").status_code in (401, 403)


def test_blocking_a_user_ends_his_session_immediately(as_user, admin, student_a):
    s, a = as_user(student_a), as_user(admin)
    assert s.get("/api/auth/me/").status_code == 200
    assert a.post(f"/api/admin/users/{student_a.pk}/block/").status_code == 200
    assert s.get("/api/auth/me/").status_code in (401, 403)


def test_django_admin_login_form_works_with_uid(admin, client):
    assert client.login(username="boss", password=PW)


# ---- admin actions -----------------------------------------------------------------------
def test_admin_approve_block_unblock_delete(as_user, admin, sec_a):
    u = make("S-9", Role.STUDENT, section=sec_a, status=Status.PENDING)
    a = as_user(admin)
    for action, expected in (("approve", "Approved"), ("block", "Blocked"), ("unblock", "Approved")):
        r = a.post(f"/api/admin/users/{u.pk}/{action}/")
        assert r.status_code == 200 and r.json()["status"] == expected
    assert a.post(f"/api/admin/users/{u.pk}/explode/").status_code == 400
    assert a.delete(f"/api/admin/users/{u.pk}/").status_code == 204
    assert not User.objects.filter(pk=u.pk).exists()


def test_admin_cannot_touch_admin_accounts(as_user, admin):
    other = make("boss2", Role.ADMIN)
    a = as_user(admin)
    assert a.delete(f"/api/admin/users/{other.pk}/").status_code == 404
    assert a.post(f"/api/admin/users/{other.pk}/block/").status_code == 404


def test_non_admins_cannot_use_admin_endpoints(anon, as_user, teacher, student_a):
    for who in (anon, as_user(teacher), as_user(student_a)):
        assert who.post(f"/api/admin/users/{student_a.pk}/approve/").status_code in (401, 403)
        assert who.delete(f"/api/admin/users/{student_a.pk}/").status_code in (401, 403)
        assert who.get("/api/admin/users/").status_code in (401, 403)
    student_a.refresh_from_db()
    assert User.objects.filter(pk=student_a.pk).exists()


def test_admin_user_list_filters(as_user, admin, teacher, student_a):
    a = as_user(admin)
    assert {u["uid"] for u in a.get("/api/admin/users/?role=teacher").json()["results"]} == {"T-1"}
    assert a.get("/api/admin/users/?search=s-1").json()["count"] == 1
