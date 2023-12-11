from django.urls import path
from .views import *

urlpatterns = [
    path("register_user/", RegistrationView.as_view(), name="register-user"),
    path("login_user/", LoginUserView.as_view(), name="login-user"),
    path("verify_user/", VerifyUserView.as_view(), name="verify-user"),
    path("get_user/", GetUserView.as_view(), name="get-user"),
    path("update_user_email/", UpdateUserEmailView.as_view(), name="update-user-email"),
    path("update_user_phone_number/", UpdateUserPhoneNumberView.as_view(), name="update-user-phone-number"),
    path("update_user_details/", UpdateUserDetailsView.as_view(), name="update-user-phone-details"),
    path("update_user_address/", UpdateUserAddressView.as_view(), name="update-user-address"),
    path("delete_user/", DeleteUserView.as_view(), name="delete-user"),
]