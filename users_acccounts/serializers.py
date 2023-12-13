from rest_framework import serializers
from .models import User, Address, Restaurant, Location
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken, TokenError


# Define serializer for user registration
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "last_name", "first_name", "email", "phone_number", "is_vendor"]


    # Method to create a new user based on the validated data
    def create(self, validated_data):
        # Return the created user
        user = User.objects.create_user(
            email=validated_data["email"],
            first_name=validated_data.get("first_name"),
            last_name=validated_data.get("last_name"),
            phone_number=validated_data.get("phone_number"),
            is_vendor=validated_data.get("is_vendor")
        )

        return user
    

# Define serializer for user verification
class VerifyUserSerializers(serializers.ModelSerializer):
    class Meta:
        model = User 
        fields = ("id", "full_name", "email", "phone_number", "is_vendor" "access_token", "refresh_token")


# Define serializer for email update
class  UpdateUserEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

    
# Define serializer for phone number update
class  UpdateUserPhoneNumberSerializer(serializers.Serializer):
    phone_number = serializers.CharField()


# Define serializer for address
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ["id", "street", "city", "state", "latitude", "longitude"]

    
# Define serializer for user detail update
class UpdateUserDetailsSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    is_vendor = serializers.BooleanField(required=False)

    def update(self, instance, validated_data):
        # Update the instance with the validated data
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.is_vendor = validated_data.get("is_vendor", instance.is_vendor)
        
        # Save the updated instance
        instance.save()

        return instance


# Define serializer for Restaurant
class RestaurantSerializer(serializers.ModelSerializer):
    hashed_verification_code = serializers.CharField(max_length=200, required=False, allow_blank=True)

    class Meta:
        model = Restaurant
        fields = ["id", "name", "description", "phone_number", "email", "opening_hours", "closing_hours", "days_of_operation", "hashed_verification_code"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Exclude 'hashed_verification_code' from the serialized data
        data.pop('hashed_verification_code', None)
        return data

    def save(self, user):
        # Assuming your Restaurant model has a 'user' field
        return Restaurant.objects.create(
            user=user,
            hashed_verification_code=self.validated_data.get('hashed_verification_code'),
            name=self.validated_data.get("name"),
            description=self.validated_data.get("description"),
            phone_number=self.validated_data.get("phone_number"),
            email=self.validated_data.get("email"),
            opening_hours=self.validated_data.get("opening_hours"),
            closing_hours=self.validated_data.get("closing_hours"),
            days_of_operation=self.validated_data.get("days_of_operation")
            # Include other fields here...
        )


# Define serializer for Location
class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["id", "street", "city", "state", "latitude", "longitude"]



# Define serializer for reataurant detail update
# class UpdateRestaurantDetailsSerializer(serializers.Serializer):
#     name = serializers.CharField(required=False)
#     description = serializers.CharField(required=False)
#     opening_hours = serializers.TimeField(required=False)
#     closing_hours = serializers.TimeField(required=False)
#     days_of_operation = serializers.CharField(required=False)
#     email = serializers.EmailField(required=False)  

#     def update(self, instance, validated_data):
#         # Update the instance with the validated data
#         instance.name = validated_data.get("name", instance.name)
#         instance.description = validated_data.get("description", instance.description)
#         instance.opening_hours = validated_data.get("opening_hours", instance.opening_hours)
#         instance.closing_hours = validated_data.get("closing_hours", instance.closing_hours)
#         instance.days_of_operation = validated_data.get("days_of_operation", instance.days_of_operation)
    
        
#         # Save the updated instance
#         instance.save()

#         return instance

    
# Define serializer for user logout
class LogoutUserSerializer(serializers.Serializer):
    refresh_token=serializers.CharField()

    default_error_message = {
        'bad_token': ('Token is expired or invalid')
    }

    def validate(self, attrs):
        self.token = attrs.get('refresh_token')

        return attrs

    def save(self, **kwargs):
        try:
            token=RefreshToken(self.token)
            token.blacklist()
        except TokenError:
            return self.fail('bad_token')


    