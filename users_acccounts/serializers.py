from rest_framework import serializers
from .models import User, Address
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken, TokenError



# Define serializer for user registration
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["uuid", "last_name", "first_name", "email", "phone_number", "is_vendor"]


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
        fields = ("uuid", "full_name", "email", "phone_number", "is_vendor" "access_token", "refresh_token")


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
        fields = ["uuid", "street", "city", "state", "latitude", "longitude"]

        # extra_kwargs = {
        #     'street': {'required': False},
        #     'city': {'required': False},
        #     'state': {'required': False},
        #     'latitude': {'required': False},
        #     'longitude': {'required': False},
        # }

    


# Define serializer for user detail update
class UpdateUserDetailsSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    is_vendor = serializers.BooleanField(required=False)

    def update(self, instance, validated_data):
        # Update the instance with the validated data
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.is_vendor = validated_data.get('is_vendor', instance.is_vendor)
        
        # Save the updated instance
        instance.save()

        return instance


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


    