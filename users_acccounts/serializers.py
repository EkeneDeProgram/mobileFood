from rest_framework import serializers
from .models import User, Address, Restaurant, Location, Category, Menu, Cart, Order
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.gis.geos import Point


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

    
class PointSerializer(serializers.BaseSerializer):
    def to_representation(self, obj):
        if obj:
            return {'longitude': obj.x, 'latitude': obj.y}
        return None

    def to_internal_value(self, data):
        if data and 'longitude' in data and 'latitude' in data:
            return Point(x=data['longitude'], y=data['latitude'])
        return None
    

# Define serializer for address
class AddressSerializer(serializers.ModelSerializer):
    point = PointSerializer(required=False)

    class Meta:
        model = Address
        fields = ["id", "street", "city", "state", "latitude", "longitude", "point"]

        extra_kwargs = {
            "latitude": {"required": False},
            "longitude": {"required": False},
        }

       
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


# Define serializer for location
class LocationSerializer(serializers.ModelSerializer):
    point = PointSerializer(required=False)
    
    class Meta:
        model = Location
        fields = ["id", "street", "city", "state", "latitude", "longitude", "point"]

        extra_kwargs = {
            "latitude": {"required": False},
            "longitude": {"required": False},

        }


# Define serializer for Restaurant
class RestaurantSerializer(serializers.ModelSerializer):
    locations = LocationSerializer(many=True, read_only=True)

    class Meta:
        model = Restaurant
        fields = ["id", "name", "description", "phone_number", "email", "opening_hours", "closing_hours", "days_of_operation", "locations"]

        
    def to_representation(self, instance):
        # Check if 'instance' is an OrderedDict (serialized data) or a model instance
        if isinstance(instance, dict):
            # If it's an OrderedDict, return it as is
            return instance
        # Access the 'location' field directly from the Restaurant instance
        location_instance = instance.location
        # Check if 'location' is an instance of Location, convert it to a dict
        if location_instance:
            location_data = LocationSerializer(location_instance).data
        else:
            location_data = None
        # Manually include the serialized location
        data = super().to_representation(instance)
        data["location"] = location_data
        return data
        

    def save(self, user):
        return Restaurant.objects.create(
            user=user,
            name=self.validated_data.get("name"),
            description=self.validated_data.get("description"),
            phone_number=self.validated_data.get("phone_number"),
            email=self.validated_data.get("email"),
            opening_hours=self.validated_data.get("opening_hours"),
            closing_hours=self.validated_data.get("closing_hours"),
            days_of_operation=self.validated_data.get("days_of_operation")
            
        )

# Define serializer for restaurant detail update
class UpdateRestaurantDetailsSerializer(serializers.Serializer):
    name  = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    phone_number = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    opening_hours = serializers.TimeField(required=False)
    closing_hours = serializers.TimeField(required=False)
    days_of_operation = serializers.CharField(required=False)


    def update(self, instance, validated_data):
        # Update the instance with the validated data
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.phone_number = validated_data.get("phone_number", instance.phone_number)
        instance.email = validated_data.get("email", instance.email)
        instance.opening_hours = validated_data.get("opening_hours", instance.opening_hours)
        instance.closing_hours = validated_data.get("closing_hours", instance.closing_hours)
        instance.days_of_operation = validated_data.get("days_of_operation", instance.days_of_operation)
        
        # Save the updated instance
        instance.save()

        return instance


# Category model serializer
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "description")

    
# MenuItem model serializer
class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = ("id",  "name", "description", "price", "category")


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ["id", "user", "item", "quantity", "created_at"]
        read_only_fields = ["id", "created_at"]  


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "user", "item", "status", "quantity", "price", "order_date", "delivered", "paid_for", "cancel"]
        read_only_fields = ["id", "order_date"]

    def create(self, validated_data):
        # Custom create method to calculate the price based on the quantity and item price
        quantity = validated_data.get("quantity", 1)
        item = validated_data["item"]
        item_price = item.price  

        total_price = item_price * quantity

        validated_data["price"] = total_price
        return super().create(validated_data)


# Define serializer for user logout
class LogoutUserSerializer(serializers.Serializer):
    refresh_token=serializers.CharField()

    default_error_message = {
        "bad_token": ("Token is expired or invalid")
    }

    def validate(self, attrs):
        self.token = attrs.get("refresh_token")

        return attrs

    def save(self, **kwargs):
        try:
            token=RefreshToken(self.token)
            token.blacklist()
        except TokenError:
            return self.fail("bad_token")

