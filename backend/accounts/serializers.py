import re

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers

from school.models import Section
from school.utils import display_subject

from .models import Role, Status, User

MOBILE_RE = re.compile(r"^[0-9+\-\s]{7,15}$")


class UserSerializer(serializers.ModelSerializer):
    """The signed-in user (login and /auth/me/)."""
    subject = serializers.SerializerMethodField()
    sections = serializers.SerializerMethodField()
    section = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "uid", "role", "full_name", "subject", "sections", "section", "father_name")

    def get_subject(self, u):
        return display_subject(u.subject)

    def get_sections(self, u):
        return [s.label for s in u.sections.all()] if u.role == Role.TEACHER else []

    def get_section(self, u):
        return u.section.label if u.section else None


def _class_or_subject(u):
    if u.role == Role.TEACHER:
        labels = ", ".join(s.label for s in u.sections.all())
        return f"{display_subject(u.subject)} ({labels})" if labels else display_subject(u.subject)
    return u.section.label if u.section else ""


class PublicUserSerializer(serializers.ModelSerializer):
    """Public live table. Deliberately NO email, mobile or password."""
    name = serializers.CharField(source="full_name")
    info = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "role", "uid", "name", "info", "status")

    def get_info(self, u):
        return _class_or_subject(u)


class AdminUserSerializer(PublicUserSerializer):
    class Meta(PublicUserSerializer.Meta):
        fields = PublicUserSerializer.Meta.fields + ("mobile", "email", "father_name", "created_at")


class RegisterSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=[Role.TEACHER, Role.STUDENT])
    uid = serializers.CharField(max_length=40)
    full_name = serializers.CharField(max_length=120)
    subject = serializers.CharField(max_length=80, required=False, allow_blank=True)
    father_name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    mobile = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)
    section = serializers.PrimaryKeyRelatedField(queryset=Section.objects.all(), required=False, allow_null=True)
    sections = serializers.PrimaryKeyRelatedField(queryset=Section.objects.all(), many=True, required=False)

    def validate_uid(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Enter the ID given by the school.")
        if value.lower() == "admin" or User.objects.filter(uid__iexact=value).exists():
            raise serializers.ValidationError("This ID is already registered.")
        return value

    def validate_mobile(self, value):
        if not MOBILE_RE.match(value.strip()):
            raise serializers.ValidationError("Enter a valid mobile number.")
        return value.strip()

    def validate(self, data):
        errors = {}
        if data["password"] != data["confirm_password"]:
            errors["confirm_password"] = "Passwords do not match."
        try:
            validate_password(data["password"])
        except DjangoValidationError as exc:
            errors["password"] = list(exc.messages)
        if data["role"] == Role.TEACHER:
            if not (data.get("subject") or "").strip():
                errors["subject"] = "Enter the subject you teach."
            if not data.get("sections"):
                errors["sections"] = "Select at least one class / section."
        else:
            if not (data.get("father_name") or "").strip():
                errors["father_name"] = "Enter your father's name."
            if not data.get("section"):
                errors["section"] = "Select your class / section."
        if errors:
            raise serializers.ValidationError(errors)
        return data

    def create(self, data):
        user = User(uid=data["uid"], role=data["role"], full_name=data["full_name"].strip(),
                    mobile=data["mobile"], email=data["email"], status=Status.PENDING)
        if user.role == Role.TEACHER:
            user.subject = data["subject"]
        else:
            user.father_name = data["father_name"].strip()
            user.section = data["section"]
        user.set_password(data["password"])
        try:
            with transaction.atomic():
                user.save()
                if user.role == Role.TEACHER:
                    user.sections.set(data["sections"])
        except IntegrityError:  # two people registering the same ID at the same moment
            raise serializers.ValidationError({"uid": "This ID is already registered."})
        return user
