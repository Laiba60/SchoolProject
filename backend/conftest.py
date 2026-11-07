import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from accounts.models import Role, Status, User
from school.models import Section

PW = "Str0ng-pass!"


@pytest.fixture(autouse=True)
def _fresh_throttle_cache():
    cache.clear()
    yield


@pytest.fixture
def sec_a(db):
    return Section.objects.create(class_name="9th", section="A")


@pytest.fixture
def sec_b(db):
    return Section.objects.create(class_name="9th", section="B")


def make(uid, role, db=None, **kw):
    kw.setdefault("status", Status.APPROVED)
    kw.setdefault("full_name", uid.title())
    sections = kw.pop("sections", [])
    u = User.objects.create_user(uid, PW, role=role, **kw)
    if sections:
        u.sections.set(sections)
    return u


@pytest.fixture
def admin(db):
    return make("boss", Role.ADMIN, is_staff=True, is_superuser=True)


@pytest.fixture
def teacher(sec_a):  # English, section A only
    return make("T-1", Role.TEACHER, subject="English", sections=[sec_a], email="t@x.com", mobile="0300111")


@pytest.fixture
def teacher2(sec_b):  # Math, section B only
    return make("T-2", Role.TEACHER, subject="Math", sections=[sec_b])


@pytest.fixture
def student_a(sec_a):
    return make("S-1", Role.STUDENT, section=sec_a, father_name="Dad", email="s@x.com", mobile="0300222")


@pytest.fixture
def student_a2(sec_a):
    return make("S-3", Role.STUDENT, section=sec_a, father_name="Dad")


@pytest.fixture
def student_b(sec_b):
    return make("S-2", Role.STUDENT, section=sec_b, father_name="Dad")


@pytest.fixture
def as_user(db):
    def _login(user):
        c = APIClient()
        c.force_login(user)
        return c
    return _login


@pytest.fixture
def anon():
    return APIClient()
