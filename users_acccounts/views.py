from rest_framework.generics import CreateAPIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated


# Import project modules
from .serializers import *
from .models import User#, Address
from utils import *

# Create your views here.

# Define view to create/register user
class RegistrationView(CreateAPIView):
    serializer_class = UserSerializer # Specify the serializer class

    # Define method that handles the POST request for user registration.
    def create(self, request):
        serializer = self.get_serializer(data=request.data) # Create an instance of the UserSerializer class
        if serializer.is_valid():
            user = User.objects.create_user(**serializer.validated_data)

            verification_code = generate_verification_code() # Generate verification code for user
            hash_verification_code = hash_VC(verification_code) # Hash verification code

            # Update and save user details
            user.hashed_verification_code = hash_verification_code 
            user.save()

            # Send email verification code 
            email = user.email
            send_verification_email(email, verification_code)

            # Serialize the user data, including the 'id' field
            serialized_data = UserSerializer(user).data

            return Response({
                "User_detail": serialized_data,
                "Message": f"{user.full_name} a verification code has been sent to {user.email}",
            },   status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


# Define view to login user with email
class LoginUserView(APIView):
    def post(self, request):
        # Get the user's input email from the request
        email = request.data.get("email") 

        # Check if the email exists in the database
        user = get_user_model().objects.filter(email=email).first()

        if user:
            # Check if the user is not deleted and not blocked
            if not user.deleted and not user.block:
                if user.is_verified:
                    verification_code = generate_verification_code() # Generate verification code for user
                    hash_verification_code = hash_VC(verification_code) # Hash verification code

                    # Update and save user details
                    user.hashed_verification_code = hash_verification_code 
                    user.save()

                    # Send email verification code 
                    email = user.email
                    send_verification_email(email, verification_code)

                    return Response({
                        "Message": f"{user.full_name} a verification code has been sent to {user.email}",
                    },  status=status.HTTP_200_OK)
                else:
                    return Response({"Message": f"{user.full_name} your account has not been verified"})
            else:
                return Response({"Message": "Your account has been blocked/deleted"})
        else:    
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        

    
class VerifyUserView(APIView):
    serializer_class = VerifyUserSerializers

    def post(self, request):
        # Get the verification code from the request data
        verification_code = request.data.get("verification_code")

        # Hash the verification code
        hashed_verification_code = hash_VC(verification_code)

        # Authenticate the user using the hashed verification code
        user = authenticate(request, hashed_verification_code=hashed_verification_code)

        if not user:
            raise AuthenticationFailed(_("Invalid verification code. Please try again."))

        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
       

        # Save the tokens to the user instance
        user.access_token = access_token
        user.refresh_token = refresh_token
        user.is_verified = True
        user.is_active = True
        user.save()

        # Create a dictionary with user information and tokens
        response_data = {
            "uuid": user.uuid,
            "full_name": user.full_name,
            "email": user.email,
            "phone_number": user.phone_number,
            "is_vendor": user.is_vendor,
            "access_token": user.access_token,
            "refresh_token": user.refresh_token,
            
        }

        return Response(response_data, status=status.HTTP_200_OK)
    
    

class GetUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Create a dictionary with user information and additional data
        response_data = {
            "uuid": user.uuid,
            "full_name": user.full_name,
            "email": user.email,
            "phone_number": user.phone_number,
            "is_vendor": user.is_vendor,
        }

        return Response(response_data, status=status.HTTP_200_OK)


