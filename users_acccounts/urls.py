from django.urls import path
from .views import *

urlpatterns = [
    path("register_user/", RegistrationView.as_view(), name="register-user"),
    path("login_user/", LoginUserView.as_view(), name="login-user"),
    path("verify_user/", VerifyUserView.as_view(), name="verify-user"),
    path("get_user/", GetUserView.as_view(), name="get-user"),
]