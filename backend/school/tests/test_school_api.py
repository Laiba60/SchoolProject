import io

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

from school.models import Section, SiteSettings


def test_sections_are_public(anon, sec_a, sec_b):
    r = anon.get("/api/sections/").json()["results"]
    assert [s["label"] for s in r] == ["9th-A", "9th-B"]


def test_admin_creates_sections_and_non_admin_cannot(as_user, admin, teacher):
    r = as_user(admin).post("/api/admin/sections/", {"class_name": "10th", "sections": ["a", "B"]}, format="json")
    assert r.status_code == 201 and {s["label"] for s in r.json()} == {"10th-A", "10th-B"}
    assert as_user(admin).post("/api/admin/sections/", {"class_name": "6th", "sections": [""]}, format="json").json()[0]["label"] == "6th"
    assert as_user(teacher).post("/api/admin/sections/", {"class_name": "x"}, format="json").status_code == 403


def test_cannot_delete_section_in_use(as_user, admin, teacher, student_a, sec_b):
    a = as_user(admin)
    assert a.delete(f"/api/admin/sections/{student_a.section.pk}/").status_code == 400
    assert a.delete(f"/api/admin/sections/{sec_b.pk}/").status_code == 204
    assert not Section.objects.filter(pk=sec_b.pk).exists()


def test_branding_upload_and_size_limit(as_user, admin, tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    buf = io.BytesIO()
    Image.new("RGBA", (20, 20), "navy").save(buf, "PNG")
    f = SimpleUploadedFile("logo.png", buf.getvalue(), content_type="image/png")
    a = as_user(admin)
    r = a.post("/api/admin/branding/", {"school_name": "COE Test", "logo": f}, format="multipart")
    assert r.status_code == 200 and r.json()["logo_url"].endswith(".png")
    assert SiteSettings.load().school_name == "COE Test"
    bad = SimpleUploadedFile("x.png", b"not an image", content_type="image/png")
    assert a.post("/api/admin/branding/", {"logo": bad}, format="multipart").status_code == 400
