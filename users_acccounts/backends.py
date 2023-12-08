from django.contrib.auth.backends import ModelBackend
from .models import User

class CustomBackend(ModelBackend):
    def authenticate(self, request, hashed_verification_code=None, **kwargs):
        try:
            user = User.objects.get(hashed_verification_code=hashed_verification_code)
            return user
        except User.DoesNotExist:
            print("User Not Found")

       