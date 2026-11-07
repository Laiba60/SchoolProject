from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("uid", "full_name", "role", "status", "created_at")
    list_filter = ("role", "status")
    search_fields = ("uid", "full_name")
    exclude = ("password",)  # passwords are never edited/displayed here
