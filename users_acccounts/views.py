from rest_framework.generics import CreateAPIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance



# Import project modules
from .serializers import *
from .models import User
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
    


class RegisterVendorView(CreateAPIView):
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
            user.is_vendor = True 
            user.save()

            # Send email verification code 
            email = user.email
            send_verification_email(email, verification_code)

            # Serialize the user data, including the 'id' field
            serialized_data = VendorSerializer(user).data

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
                "id": user.id,
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
        

# Define view to resend verification code to user
class ResendVerificationCodeView(APIView):
    def put(self, request):
        # Get the user based on the provided email
        email = request.data.get("email")
        user = get_user_model().objects.filter(email=email).first()

        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        if not user.deleted and not user.block:
            # Check if the user is already verified
            if user.is_verified:
                return Response({"detail": "User is already verified"}, status=status.HTTP_400_BAD_REQUEST)

            # Generate and save a new verification code
            verification_code = generate_verification_code()
            hash_verification_code = hash_VC(verification_code)

            user.hashed_verification_code = hash_verification_code
            user.save()

            # Send the new verification code via email
            send_verification_email(email, verification_code)

            return Response({"message": f"{user.full_name} Verification code resent successfully to {user.email}"}, status=status.HTTP_200_OK)
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})
        



# Define view to get user data
class GetUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        
            user = request.user

            if not user.deleted and not user.block:
                if not user.is_verified:
                    return Response({"Message": f"{user.full_name} your account has not been verified"})

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
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})

            serializer = UpdateUserEmailSerializer(data=request.data)
            if serializer.is_valid():
                email = serializer.validated_data.get("email")

                # Ensure email is not None or an empty string
                if email:

                    # Check if the email already exists in the database
                    if User.objects.filter(email=email).exclude(id=user.id).exists():
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
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})

            serializer = UpdateUserPhoneNumberSerializer(data=request.data)
            if serializer.is_valid():
                phone_number = serializer.validated_data.get("phone_number")

                # Ensure phone_number is not None or an empty string
                if phone_number:

                    # Check if the phone_number already exists in the database
                    if User.objects.filter(phone_number=phone_number).exclude(id=user.id).exists():
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
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})

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
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})

            # Check if the user already has an address
            if user.address:
                # Update the existing address
                serializer = AddressSerializer(user.address, data=request.data, partial=True)
            else:
                # Create a new location
                serializer = AddressSerializer(data=request.data)

            if serializer.is_valid():
                address_instance = serializer.save(user=user)

                # Manually set the PointField based on latitude and longitude
                address_instance.point = Point(serializer.validated_data['latitude'], serializer.validated_data['longitude'])
                address_instance.save()

                # Associate the address with the user
                user.address = address_instance
                user.save()
                
                response_data = {
                    "message": "Address updated successfully",
                    "location": serializer.data,
                }

                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})


# Define view to delete user account
class DeleteUserView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                    return Response({"Message": f"{user.full_name} your account has not been verified"})

            # Update user deleted to true
            user.deleted = True
            user.is_verified = False
            user.is_active = False
            user.save()

            response_data = {
                "message": f"{user.full_name} Your account has been deleted successfully"
            }

            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})


# Define view to create restaurant
class RestaurantCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                    return Response({"Message": f"{user.full_name} your account has not been verified"})
            
            if user.is_vendor:

                serializer = RestaurantSerializer(data=request.data)

                if serializer.is_valid():
                    # Save the restaurant instance to the database
                    restaurant_instance = serializer.save(user=user) 

                    serialized_data = RestaurantSerializer(restaurant_instance).data

                    return Response({
                        "restautrant_detail": serialized_data,
                        "Message": f"{user.full_name} {restaurant_instance.name} created successfully!",
                    },   status=status.HTTP_201_CREATED)
                
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"Message": f"{user.full_name} You are not authorized to perform this operation"})
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})


# Define view to update restaurant location
class UpdateRestaurantLocationView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, restaurant_id):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})

            if user.is_vendor:

                try:
                    restaurant = Restaurant.objects.get(id=restaurant_id, user=user)
                except Restaurant.DoesNotExist:
                    return Response({"Message": "Restaurant not found or you don't have permission to update its location."}, status=status.HTTP_404_NOT_FOUND)

                if restaurant.is_active:
                    # Check if the user already has a location
                    if restaurant.location:
                        # Update the existing address
                        serializer = LocationSerializer(restaurant.location, data=request.data, partial=True)
                    else:
                        # Create a new location
                        serializer = LocationSerializer(data=request.data)

                    if serializer.is_valid():
                        Location_instance = serializer.save(restaurant=restaurant)

                        # Manually set the PointField based on latitude and longitude
                        Location_instance.point = Point(serializer.validated_data['latitude'], serializer.validated_data['longitude'])
                        Location_instance.save()

                        # Associate the address with the user
                        restaurant.location = Location_instance
                        restaurant.save()
                
                        response_data = {
                            "message": "Location updated successfully",
                            "location": serializer.data,
                        }

                        return Response(response_data, status=status.HTTP_200_OK)
                    else:
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    
                else:
                    return Response({"Message": f"Your {restaurant.name} has not been activated"}, status=status.HTTP_400_BAD_REQUEST)        
            else:
                return Response({"Message": f"{user.full_name} You are not authorized to perform this operation"})
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})



# Define view to update restaurant detail
class UpdateRestaurantDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, restaurant_id):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})
            
            if user.is_vendor:
                    try:
                        # Retrieve the restaurant instance
                        restaurant = Restaurant.objects.get(id=restaurant_id, user=user)

                        # Check if the restaurant is deleted or blocked
                        if restaurant.deleted or restaurant.block:
                            return Response({"Message": "Restaurant not found or access denied"}, status=status.HTTP_404_NOT_FOUND)

                        # Validate and update the restaurant details
                        serializer = UpdateRestaurantDetailsSerializer(restaurant, data=request.data, partial=True)

                        if serializer.is_valid():
                            serializer.save()
                            
                            # Retrieve the updated restaurant instance
                            updated_restaurant = Restaurant.objects.get(id=restaurant_id, user=user)

                            # Serialize the updated restaurant details
                            response_data = {
                                "Message": "Restaurant details updated successfully",
                                "RestaurantDetails": RestaurantSerializer(updated_restaurant).data
                            }

                            return Response(response_data, status=status.HTTP_200_OK)
                        else:
                            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                    except Restaurant.DoesNotExist:
                        return Response({"Message": "Restaurant not found or access denied"}, status=status.HTTP_404_NOT_FOUND)           
            else:
                return Response({"Message": f"{user.full_name} You are not authorized to perform this operation"})
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})



# Define view to delete restaurant 
class DeleteRestaurantView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, restaurant_id):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})
            
            if user.is_vendor:
                
                try:
                    # Get the restaurant instance
                    restaurant_instance = Restaurant.objects.get(id=restaurant_id)
                except Restaurant.DoesNotExist:
                    return Response({"Message": "Restaurant not found"}, status=status.HTTP_404_NOT_FOUND)
                
                # Check if the authenticated user is the owner of the restaurant
                if restaurant_instance.user == user:
                    if restaurant_instance.is_active:

                        # Update restaurant deleted to true and is_active to False
                        restaurant_instance.deleted = True
                        restaurant_instance.is_active = False
                        restaurant_instance.save()

                        response_data = {
                            "message": f"{restaurant_instance.name} has been deleted successfully"
                        }

                        return Response(response_data, status=status.HTTP_200_OK)
                        
                    else:
                        return Response({"Message": f"Your {restaurant_instance.name} has not been activated"})       
                else:
                    return Response({"Message": "You are not authorized to update this restaurant"}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({"Message": f"{user.full_name} You are not authorized to perform this operation"})
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})



# Define view to add item to menu
class AddMenuItemView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, restaurant_id):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                    return Response({"Message": f"{user.full_name} your account has not been verified"})
            
            if user.is_vendor:
                
                try:
                    # Ensure that the authenticated user is the owner of the restaurant
                    restaurant = Restaurant.objects.get(id=restaurant_id, user=user)
                except Restaurant.DoesNotExist:
                    return Response({"Message": "Restaurant not found or you are not the owner."}, status=status.HTTP_404_NOT_FOUND)
                
                if restaurant.is_active:

                    serializer = MenuSerializer(data=request.data)

                    if serializer.is_valid():
                        # Set the restaurant and user for the menu item before saving
                        serializer.validated_data['restaurant'] = restaurant
                        serializer.validated_data['user'] = user

                        # Create and save the menu item
                        menu_item = serializer.save()

                        # Serialize the created menu item and return it in the response
                        response_data = {
                            "message": "Menu item added successfully.",
                            "menu_item": MenuSerializer(menu_item).data,
                        }

                        return Response(response_data, status=status.HTTP_201_CREATED)
                    else:
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"Message": f"Your {restaurant.name} has not been activated"})
            else:
                return Response({"Message": f"{user.full_name} You are not authorized to perform this operation"})
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})



# Define view to update menu item
class UpdateMenuItemView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, restaurant_id, menu_item_id):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                    return Response({"Message": f"{user.full_name} your account has not been verified"})
            
            if user.is_vendor:
                
                try:
                    # Ensure that the authenticated user is the owner of the restaurant
                    restaurant = Restaurant.objects.get(id=restaurant_id, user=user)
                except Restaurant.DoesNotExist:
                    return Response({"Message": "Restaurant not found or you are not the owner."}, status=status.HTTP_404_NOT_FOUND)
                
                if restaurant.is_active:

                    try:
                        # Ensure that the menu item belongs to the specified restaurant and user
                        menu_item = Menu.objects.get(id=menu_item_id, restaurant=restaurant, user=user)
                    except Menu.DoesNotExist:
                        return Response({"Message": "Menu item not found or you are not the owner."}, status=status.HTTP_404_NOT_FOUND)


                    serializer = MenuSerializer(menu_item, data=request.data, partial=True)


                    if serializer.is_valid():

                        # Update and save the menu item
                        updated_menu_item = serializer.save()

                        # Serialize the updated menu item and return it in the response
                        response_data = {
                            "message": "Menu item updated successfully.",
                            "menu_item": MenuSerializer(updated_menu_item).data,
                        }

                        return Response(response_data, status=status.HTTP_201_CREATED)

                    else:
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"Message": f"Your {restaurant.name} has not been activated"})
            else:
                return Response({"Message": f"{user.full_name} You are not authorized to perform this operation"})
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})


# Define view to delete item from menu
class DelteMenuItemView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, restaurant_id, menu_item_id):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                    return Response({"Message": f"{user.full_name} your account has not been verified"})
            
            if user.is_vendor:
                
                try:
                    # Ensure that the authenticated user is the owner of the restaurant
                    restaurant = Restaurant.objects.get(id=restaurant_id, user=user)
                except Restaurant.DoesNotExist:
                    return Response({"Message": "Restaurant not found or you are not the owner."}, status=status.HTTP_404_NOT_FOUND)
                
                if restaurant.is_active:

                    try:
                        # Ensure that the menu item belongs to the specified restaurant and user
                        menu_item = Menu.objects.get(id=menu_item_id, restaurant=restaurant, user=user)
                    except Menu.DoesNotExist:
                        return Response({"Message": "Menu item not found or you are not the owner."}, status=status.HTTP_404_NOT_FOUND)


                    menu_item.deleted = True
                    menu_item.save()

                    response_data = {
                            "message": f"{menu_item.name} has been deleted successfully"
                        }

                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    return Response({"Message": f"Your {restaurant.name} has not been activated"})
            else:
                return Response({"Message": f"{user.full_name} You are not authorized to perform this operation"})
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})


# Define view to get all active restaurant
class ActiveRestaurantsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})

            
            # Filter restaurants based on the specified conditions
            active_restaurants = Restaurant.objects.filter(is_active=True, deleted=False, block=False)
            # Serialize the queryset
            serializer = RestaurantSerializer(active_restaurants, many=True)

            # Return the serialized data in the response
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})


# Define view to get all active restaurant created by a user
class UserActiveRestaurantsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})
            
            if user.is_vendor:
                # Filter active restaurants based on the specified user
                user_active_restaurants = Restaurant.objects.filter(user=user, is_active=True, deleted=False, block=False)

                # Serialize the queryset
                serializer = RestaurantSerializer(user_active_restaurants, many=True)

                # Return the serialized data in the response
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"Message": f"{user.full_name} You are not authorized to perform this operation"})
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})


# Define view to get restaurant by id
class RestaurantDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, restaurant_id):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})
            
            # Retrieve the restaurant object or return a 404 response if not found
            restaurant = get_object_or_404(Restaurant, id=restaurant_id, is_active=True, deleted=False, block=False)

             # Serialize the restaurant object
            serializer = RestaurantSerializer(restaurant)

            # Return the serialized data in the response
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})


# Define view to get all menu item
class AllItemsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})

            # Retrieve all items where deleted is False
            items = Menu.objects.filter(deleted=False)

            # Serialize the queryset
            serializer = MenuSerializer(items, many=True)

            # Return the serialized data in the response
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})



# Define view to get a restaurant menu
class RestaurantMenuView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, restaurant_id):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})
            
            try:
                # Retrieve the restaurant instance
                restaurant = Restaurant.objects.get(id=restaurant_id, is_active=True, deleted=False, block=False)
            except Restaurant.DoesNotExist:
                return Response({"Message": "Restaurant not found or not active"}, status=status.HTTP_404_NOT_FOUND)

            # Retrieve all items for the restaurant where deleted is False
            items = Menu.objects.filter(restaurant=restaurant, deleted=False)

            # Serialize the queryset
            serializer = MenuSerializer(items, many=True)

            # Return the serialized data in the response
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})


# Define view to get all items added by a restaurant
class RestaurantItemsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, restaurant_id):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})
            
            if user.is_vendor:
                try:
                    # Retrieve the restaurant instance
                    restaurant = Restaurant.objects.get(id=restaurant_id, is_active=True, deleted=False, block=False)
                except Restaurant.DoesNotExist:
                    return Response({"Message": "Restaurant not found or not active"}, status=status.HTTP_404_NOT_FOUND)

                # Retrieve all items for the restaurant where deleted is False
                items = Menu.objects.filter(restaurant=restaurant, deleted=False)

                # Serialize the queryset
                serializer = MenuSerializer(items, many=True)

                # Return the serialized data in the response
                return Response(serializer.data, status=status.HTTP_200_OK)
                
            else:
                return Response({"Message": f"{user.full_name} You are not authorized to perform this operation"})
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})


# Define view to get item by id
class ItemView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, menu_item_id):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})
            
            # Retrieve the item object or return a 404 response if not found
            menu_item = get_object_or_404(Menu, id=menu_item_id, deleted=False)

            # Serialize the menu item object
            serializer = MenuSerializer(menu_item)

            # Return the serialized data in the response
            return Response(serializer.data, status=status.HTTP_200_OK)     
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})


# Define view to get items by category
class ItemsByCategoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, category_id):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})
            
            try:
                # Retrieve the category instance
                category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                return Response({"Message": "category not found or not active"}, status=status.HTTP_404_NOT_FOUND)

            # Retrieve all items by category where deleted is False
            items = Menu.objects.filter(category=category, deleted=False)

            # Serialize the queryset
            serializer = MenuSerializer(items, many=True)

            # Return the serialized data in the response
            return Response(serializer.data, status=status.HTTP_200_OK)
             
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})
        

# Define view to search for restaurant 
class SearchRestaurantView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})
            
            # Get the search parameters from the request
            name = request.query_params.get("name", "")
            description = request.query_params.get("description", "")
            opening_hours = request.query_params.get("opening_hours", "")
            closing_hours = request.query_params.get("closing_hours", "")
            days_of_operation = request.query_params.get("days_of_operation", "")


            # Build the query based on the provided parameters
            query = Q(deleted=False)

            if name:
                query &= Q(name__icontains=name)
            if description:
                query &= Q(description__icontains=description)
            if opening_hours:
                query &= Q(opening_hours__icontains=opening_hours)
            if closing_hours:
                query &= Q(closing_hours__icontains=closing_hours)
            if days_of_operation:
                query &= Q(days_of_operation__icontains=days_of_operation)


            # Add a condition to filter only items where restaurant is_active is true
            query &= Q(is_active=True)

            # Search for restaurant based on the query
            restaurants = Restaurant.objects.filter(query)

            # Serialize the queryset
            serializer = RestaurantSerializer(restaurants, many=True)

            # Return the serialized data in the response
            return Response(serializer.data, status=status.HTTP_200_OK)       
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})



# Define view to search for item 
class SearchMenuView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})

            # Get the search parameters from the request
            name = request.query_params.get("name", "")
            price = request.query_params.get("price", "")
            category = request.query_params.get("category", "")
            restaurant = request.query_params.get("restaurant", "")
            description = request.query_params.get("description", "")

            # Build the query based on the provided parameters
            query = Q(deleted=False)

            if name:
                query &= Q(name__icontains=name)
            if price:
                query &= Q(price__icontains=price)
            if category:
                query &= Q(category__name__icontains=category)
            if restaurant:
                query &= Q(restaurant__name__icontains=restaurant, restaurant__user=user, restaurant__is_active=True)
            if description:
                query &= Q(description__icontains=description)


            # Add a condition to filter only items where restaurant.is_active is true
            query &= Q(restaurant__is_active=True)

            # Search for menu items based on the query
            menu_items = Menu.objects.filter(query)

            # Serialize the queryset
            serializer = MenuSerializer(menu_items, many=True)

            # Return the serialized data in the response
            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})


# Define view to search restaurant by location
class SearchRestaurantByLocationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})

            # Get the longitude and latitude from query parameters
            longitude = request.query_params.get("longitude", "")
            latitude = request.query_params.get("latitude", "")

            # Check if both longitude and latitude are provided
            if not longitude or not latitude:
                return Response({"Message": "Both longitude and latitude are required for the search."}, status=status.HTTP_400_BAD_REQUEST)

            # Create a Point object for the provided longitude and latitude
            user_location = Point(float(longitude), float(latitude), srid=4326)

            # Search for active restaurants based on the distance from the user's location
            restaurants = Restaurant.objects.filter(
                is_active=True,
                location__point__isnull=False  # Ensure the restaurant has a valid location
            ).annotate(
                distance=Distance('location__point', user_location)
            ).order_by('distance')

            # Serialize the queryset
            serializer = RestaurantSerializer(restaurants, many=True)

            # Return the serialized data in the response
            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})



# Define view to add item to cart
class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, item_id):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})

            # Try to get the item from the cart
            try:
                cart_item = Cart.objects.get(user=user, item_id=item_id)
            except Cart.DoesNotExist:
                cart_item = None

            if cart_item:
                # If the item exists, increment the quantity
                cart_item.quantity += 1
                cart_item.save()
            else:
                # If the item doesn't exist, create a new cart item
                cart_item = Cart(user=user, item_id=item_id, quantity=1)
                cart_item.save()

            serializer = CartSerializer(cart_item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})



# Define view to update cart item
class UpdateCartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, item_id):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})

            # Try to get the item from the cart
            try:
                cart_item = Cart.objects.get(user=user, item_id=item_id)
            except Cart.DoesNotExist:
                return Response({"Message": "Item not found in the cart"}, status=status.HTTP_404_NOT_FOUND)

            # Validate and update the quantity
            serializer = CartSerializer(cart_item, data=request.data, partial=True)
            if serializer.is_valid():
                cart_item.quantity = serializer.validated_data.get('quantity', cart_item.quantity)
                cart_item.save()

                updated_serializer = CartSerializer(cart_item)
                return Response(updated_serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})



# Define view to delete an item from user cart
class DeleteCartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})

            # Try to get the item from the cart
            try:
                cart_item = Cart.objects.get(user=user, item_id=item_id)
            except Cart.DoesNotExist:
                return Response({"Message": "Item not found in the cart"}, status=status.HTTP_404_NOT_FOUND)

            # Delete the item from the cart
            cart_item.delete()

            return Response({"Message": "Item deleted successfully"}, status=status.HTTP_200_OK)

        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})
        

# Define view to clear user cart
class ClearCartView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})

            # Delete all items from the user's cart
            Cart.objects.filter(user=user).delete()

            return Response({"Message": "All items deleted from the cart successfully"}, status=status.HTTP_200_OK)

        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})


# Define view to get user cart
class UserCartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})

            # Retrieve all cart items for the user
            cart_items = Cart.objects.filter(user=user)
            serializer = CartSerializer(cart_items, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})
        

# Define view to place order
class MakeOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})

            # Retrieve cart items for the user
            cart_items = Cart.objects.filter(user=user)

            if not cart_items.exists():
                return Response({"Message": "Your cart is empty. Add items before making an order."}, status=status.HTTP_400_BAD_REQUEST)

            # Create orders from cart items
            orders = []

            for cart_item in cart_items:
                order = Order(
                    user=user,
                    item=cart_item.item,
                    restaurant=cart_item.item.restaurant, 
                    quantity=cart_item.quantity,
                    price=cart_item.item.price,
                    delivered=False,
                    paid_for=False,
                    cancel=False
                )
                orders.append(order)

            # Bulk create orders
            Order.objects.bulk_create(orders)

            # Delete cart items after creating orders
            cart_items.delete()

            # Serialize the orders to return a list of ordered items with their quantity, price, and name
            order_serializer = PlaceOrderSerializer(orders, many=True)

            return Response({"message": "Order placed successfully", "ordered_items": order_serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})



# Define view to enable restaurant update order
class RestaurantUpdateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, order_id):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified or not user.is_vendor:
                return Response({"Message": f"{user.full_name} is not authorized to perform this action."},
                                status=status.HTTP_403_FORBIDDEN)

            try:
                order = Order.objects.get(id=order_id, item__restaurant__user=user, cancel=False)
            except Order.DoesNotExist:
                return Response({"Message": "Order not found or you don't have permission to update it."},
                                status=status.HTTP_404_NOT_FOUND)

            serializer = OrderSerializer(order, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Order updated successfully", "order": serializer.data})
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})


# Define view to enable user cancel an order
class CancelOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, order_id):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})

        try:
            order = Order.objects.get(id=order_id, user=user, status__lt=3, paid_for=False, delivered=False)
        except Order.DoesNotExist:
            return Response(
                {"Message": "Order not found or you don't have permission to cancel it."},
                status=status.HTTP_404_NOT_FOUND
            )

        # cancel order
        order.cancel = True
        order.save()

        return Response({"Message": "Order canceled successfully."}, status=status.HTTP_200_OK)



# Define view to get all user order
class UserOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"})

            # Retrieve all order for the user
            order_items = Order.objects.filter(user=user)
            serializer = PlaceOrderSerializer(order_items, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})
        

# Define view to get all order place with a restaurant
class RestaurantOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, restaurant_id):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified or not user.is_vendor:
                return Response(
                    {"Message": f"{user.full_name} is not authorized to perform this action."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Retrieve the restaurant
            restaurant = get_object_or_404(Restaurant, user=user, id=restaurant_id)

            # Retrieve all orders for items in the restaurant
            restaurant_orders = Order.objects.filter(restaurant=restaurant, cancel=False)
            serializer = PlaceOrderSerializer(restaurant_orders, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})        


# Define view to get order details
class OrderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        user = request.user

        if not user.deleted and not user.block:
            if not user.is_verified:
                return Response({"Message": f"{user.full_name} your account has not been verified"},
                                status=status.HTTP_400_BAD_REQUEST)

            # Retrieve the order for the user
            try:
                order_item = Order.objects.get(id=order_id, user=user)
            except Order.DoesNotExist:
                return Response(
                    {"Message": "Order not found or you don't have permission to access it."},
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = OrderSerializer(order_item)
            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"},
                            status=status.HTTP_403_FORBIDDEN)
        

# Define view to logout user 
class LogoutUserView(APIView):
    serializer_class=LogoutUserSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer=self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
 

