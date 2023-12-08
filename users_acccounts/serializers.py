from rest_framework import serializers
from .models import User
from rest_framework_simplejwt.tokens import RefreshToken, TokenError



# Define serializer for User
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
    

class VerifyUserSerializers(serializers.ModelSerializer):
    class Meta:
        model = User 
        fields = ("uuid", "full_name", "email", "phone_number", "is_vendor" "access_token", "refresh_token")



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


    