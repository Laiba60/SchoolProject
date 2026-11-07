from django.contrib.auth import get_user_model

from .models import Status


class UidBackend:
    """Authenticate by school ID (case-insensitive) + password."""

    def check_credentials(self, uid, password):
        """Return the user if uid/password are right, whatever his status.

        The login view uses this so it can give a clear message for Pending/Blocked
        accounts, but only to someone who actually knows the password.
        """
        if not uid or not password:
            return None
        User = get_user_model()
        user = User.objects.filter(uid__iexact=str(uid).strip()).first()
        if user is None:
            # Run the hasher anyway so timing does not reveal whether the ID exists.
            User().set_password(password)
            return None
        return user if user.check_password(password) else None

    def authenticate(self, request, uid=None, password=None, username=None, **kwargs):
        # Django's admin login form passes `username=`; the API passes `uid=`.
        user = self.check_credentials(uid or username, password)
        if user is not None and user.is_active and user.status == Status.APPROVED:
            return user
        return None

    def get_user(self, user_id):
        User = get_user_model()
        user = User.objects.filter(pk=user_id).first()
        # Re-checked on every request: blocking a user ends his session immediately.
        if user and user.is_active and user.status == Status.APPROVED:
            return user
        return None

    # Needed so Django admin (superuser) permission checks work.
    def has_perm(self, user_obj, perm, obj=None):
        return user_obj.is_active and user_obj.is_superuser

    def has_module_perms(self, user_obj, app_label):
        return user_obj.is_active and user_obj.is_superuser
