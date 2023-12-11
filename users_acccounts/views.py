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
                return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})
        else:    
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        

# Define view to verify user with verification code    
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

        if not user.deleted and not user.block:
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
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})
        
        
# Define view to get user data
class GetUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if not user.deleted and not user.block:

            # Create a dictionary with user information and additional data
            serializer = UserSerializer(user)
            address_serializer = AddressSerializer(user.address)

            response_data = {
                "user": serializer.data,
                "address": address_serializer.data,
            }

            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})


# Define view to update user email
class UpdateUserEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user

        if not user.deleted and not user.block:

            serializer = UpdateUserEmailSerializer(data=request.data)
            if serializer.is_valid():
                email = serializer.validated_data.get("email")

                # Ensure email is not None or an empty string
                if email:

                    # Check if the email already exists in the database
                    if User.objects.filter(email=email).exclude(uuid=user.uuid).exists():
                        return Response({"error": "This email is already in use by another user."},
                                        status=status.HTTP_400_BAD_REQUEST)
                    
                    verification_code = generate_verification_code()
                    hash_verification_code = hash_VC(verification_code)

                    # Update user details
                    user.email = email
                    user.is_verified = False
                    user.hashed_verification_code = hash_verification_code
                    user.save()

                    # Send email verification code
                    send_verification_email(email, verification_code)

                    response_data = {
                        "message": f"{user.full_name} a verification code has been sent to {user.email}",
                        "email": f"{user.email}",
                    }

                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "email cannot be null or empty"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})



# Define view to update user phone number
class UpdateUserPhoneNumberView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user

        if not user.deleted and not user.block:

            serializer = UpdateUserPhoneNumberSerializer(data=request.data)
            if serializer.is_valid():
                phone_number = serializer.validated_data.get("phone_number")

                # Ensure phone_number is not None or an empty string
                if phone_number:

                    # Check if the phone_number already exists in the database
                    if User.objects.filter(phone_number=phone_number).exclude(uuid=user.uuid).exists():
                        return Response({"error": "This phone number is already in use by another user."},
                                        status=status.HTTP_400_BAD_REQUEST)
                    

                    user.phone_number = phone_number
                    user.save()

                    response_data = {
                        "message": f"{user.full_name} your phone number has been updated successfully",
                        "phone_number": f"{user.phone_number}",
                    }

                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "phone number cannot be null or empty"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})


# Define view to update user detail
class UpdateUserDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user

        if not user.deleted and not user.block:

            serializer = UpdateUserDetailsSerializer(data=request.data, partial=True)
            if serializer.is_valid():
                # Update user details
                serializer.update(user, serializer.validated_data)
                user = User.objects.create_user(**serializer.validated_data)

                # Serialize the updated user and return it in the response
                updated_user_serializer = UpdateUserDetailsSerializer(user)
                return Response({"message": "User details updated successfully.", "user": updated_user_serializer.data},
                                    status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})


# Define view to update user address
class UpdateUserAddressView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        
        if not user.deleted and not user.block:
            street = request.data.get("street")
            city = request.data.get("city")
            state = request.data.get("state")
            latitude = request.data.get("latitude")
            longitude = request.data.get("longitude")
            

            # Check if the user already has an address
            if user.address:
                # Update only the specified address fields
                if street:
                    user.address.street = street
                if city:
                    user.address.city = city
                if state:
                    user.address.state = state
                if latitude:
                    user.address.latitude = latitude
                if longitude:
                    user.address.longitude = longitude
                    
                user.address.save()
            else:
                
                # If the user does not have an associated address, create one
                address = Address.objects.create(street=street, city=city, state=state, latitude=latitude, longitude=longitude)
                user.address = address
                user.save()

            # Serialize the updated address details
            address_serializer = AddressSerializer(user.address)
            response_data = {
                "message": "Address updated successfully",
                "address": address_serializer.data,
            }

            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})


# Define view to delete user account
class DeleteUserView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user

        # Update user deleted to true
        user.deleted = True
        user.is_verified = False
        user.is_active = False
        user.save()

        response_data = {
            "message": f"{user.full_name} Your account has been deleted successfully"
        }

        return Response(response_data, status=status.HTTP_200_OK)


# Define view to logout user 
class LogoutUserView(APIView):
    serializer_class=LogoutUserSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer=self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
 

