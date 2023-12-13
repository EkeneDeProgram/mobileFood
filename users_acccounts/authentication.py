from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import User 
import jwt



class UserAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # Get the authorization header from the request
        authorization_header = request.headers.get('Authorization')

        if not authorization_header or 'Bearer' not in authorization_header:
            return None

        # Get the access token from the authorization header
        access_token = authorization_header.split()[1]

        try:
            # Decode the access token
            decoded_token = AccessToken(access_token, verify=False).payload
            user_id = decoded_token["user_id"]

            # Implement logic to retrieve the vendor based on vendor_id
            user = User.objects.get(id=user_id)

            # Return a tuple of (user, None) to indicate successful authentication
            return user, None

        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Access token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid access token')
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found')