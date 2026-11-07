from django.core.management.base import BaseCommand

from school.models import Section, SiteSettings

DEFAULT_SECTIONS = [("9th", "A"), ("9th", "B"), ("10th", "A"), ("10th", "B")]


class Command(BaseCommand):
    help = "Create the default sections (9th-A, 9th-B, 10th-A, 10th-B) and the site settings row. Safe to re-run."

    def handle(self, *args, **options):
        created = 0
        for class_name, section in DEFAULT_SECTIONS:
            _, was_created = Section.objects.get_or_create(class_name=class_name, section=section)
            created += was_created
        SiteSettings.load()
        self.stdout.write(self.style.SUCCESS(
            f"Sections ready ({created} created, {len(DEFAULT_SECTIONS) - created} already existed)."
        ))
