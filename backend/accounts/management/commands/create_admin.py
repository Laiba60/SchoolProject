import os
from getpass import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from accounts.models import Role, Status


class Command(BaseCommand):
    help = (
        "Create (or reset the password of) the admin account. "
        "ID and password come from --uid/ADMIN_UID and ADMIN_PASSWORD, or are prompted."
    )

    def add_arguments(self, parser):
        parser.add_argument("--uid", help="Admin login ID (default: env ADMIN_UID or prompt)")
        parser.add_argument("--full-name", default="Administrator")

    def handle(self, *args, **opts):
        User = get_user_model()
        uid = (opts["uid"] or os.environ.get("ADMIN_UID") or input("Admin ID: ")).strip()
        if not uid:
            raise CommandError("Admin ID is required.")

        password = os.environ.get("ADMIN_PASSWORD")
        if not password:
            password = getpass("Password: ")
            if password != getpass("Confirm password: "):
                raise CommandError("Passwords do not match.")

        try:
            validate_password(password)
        except ValidationError as exc:
            raise CommandError("; ".join(exc.messages))

        existing = User.objects.filter(uid__iexact=uid).first()
        if existing and existing.role != Role.ADMIN:
            raise CommandError(f"ID '{uid}' already belongs to a {existing.role}.")

        if existing:
            existing.set_password(password)
            existing.status = Status.APPROVED
            existing.is_staff = existing.is_superuser = True
            existing.save()
            self.stdout.write(self.style.SUCCESS(f"Admin '{existing.uid}' updated."))
        else:
            User.objects.create_superuser(uid, password, full_name=opts["full_name"])
            self.stdout.write(self.style.SUCCESS(f"Admin '{uid}' created."))
