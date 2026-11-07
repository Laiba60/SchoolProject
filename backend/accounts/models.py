from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone

from school.utils import normalize_subject


class Role(models.TextChoices):
    TEACHER = "teacher", "Teacher"
    STUDENT = "student", "Student"
    ADMIN = "admin", "Admin"


class Status(models.TextChoices):
    PENDING = "Pending", "Pending"
    APPROVED = "Approved", "Approved"
    BLOCKED = "Blocked", "Blocked"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create(self, uid, password, **extra):
        uid = (uid or "").strip()
        if not uid:
            raise ValueError("The uid must be set.")
        user = self.model(uid=uid, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, uid, password=None, **extra):
        extra.setdefault("role", Role.STUDENT)
        return self._create(uid, password, **extra)

    def create_superuser(self, uid, password=None, **extra):
        extra.update(
            role=Role.ADMIN, status=Status.APPROVED, is_staff=True, is_superuser=True,
        )
        extra.setdefault("full_name", "Administrator")
        return self._create(uid, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    uid = models.CharField("School ID", max_length=40, unique=True)
    role = models.CharField(max_length=10, choices=Role.choices)
    full_name = models.CharField(max_length=120)
    subject = models.CharField(max_length=80, blank=True)       # teachers (normalized)
    father_name = models.CharField(max_length=120, blank=True)  # students
    mobile = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    # PROTECT: a section cannot be deleted while students belong to it.
    section = models.ForeignKey(
        "school.Section", null=True, blank=True, on_delete=models.PROTECT, related_name="students",
    )
    sections = models.ManyToManyField("school.Section", blank=True, related_name="teachers")
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    # Django plumbing. Access is gated by `status`, so is_active stays True.
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "uid"
    REQUIRED_FIELDS = []
    objects = UserManager()

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            # IDs are unique ignoring case ("T01" == "t01").
            models.UniqueConstraint(Lower("uid"), name="user_uid_ci_unique"),
        ]
        indexes = [
            models.Index(fields=["role", "status"]),
            models.Index(fields=["role", "created_at"]),
        ]

    def save(self, *args, **kwargs):
        self.uid = (self.uid or "").strip()
        if self.role == Role.TEACHER:
            self.subject = normalize_subject(self.subject)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.uid} ({self.role})"
