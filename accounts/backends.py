from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class ApprovalBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        if not user.check_password(password):
            return None

        if user.is_superuser or user.is_staff:
            return user

        if not user.is_approved:
            if request:
                request._login_blocked_reason = 'pending_approval'
            return None

        return user