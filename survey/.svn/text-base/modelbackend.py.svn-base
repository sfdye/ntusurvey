from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class EmailBackend(ModelBackend):
    """A django.contrib.auth backend that authenticates the user based on its
     email address instead of the username.
     """

    def authenticate(self, email=None, password=None):
        """Authenticate user using its email address instead of username."""
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None