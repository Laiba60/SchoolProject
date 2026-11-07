from django.core.exceptions import ValidationError
from django.db import models


class Section(models.Model):
    class_name = models.CharField(max_length=20)   # e.g. "9th"
    section = models.CharField(max_length=10)      # e.g. "B"

    class Meta:
        ordering = ["class_name", "section"]
        constraints = [
            models.UniqueConstraint(fields=["class_name", "section"], name="section_unique_class_section"),
        ]

    @property
    def label(self):
        return f"{self.class_name}-{self.section}" if self.section else self.class_name

    def __str__(self):
        return self.label


class SiteSettings(models.Model):
    """Single-row table holding branding (school name + logo)."""

    school_name = models.CharField(max_length=120, default="CENTER OF EXCELLENCE")
    logo = models.ImageField(upload_to="branding/", blank=True)

    class Meta:
        verbose_name_plural = "Site settings"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1  # enforce the single row
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Site settings cannot be deleted.")

    def __str__(self):
        return self.school_name
