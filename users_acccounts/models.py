from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from phonenumbers import parse
from .managers import UserManager
from django.contrib.gis.db import models




# Define model for address
class Address(models.Model):
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    point = models.PointField(blank=True, null=True)


# Define model for user
class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=255, verbose_name=_("First Name"))
    last_name = models.CharField(max_length=255, verbose_name=_("Last Name"))
    email = models.EmailField(max_length=225, unique=True, verbose_name=_("Email Address"))
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True, verbose_name=_("Phone Number"))
    is_vendor = models.BooleanField(default=False, verbose_name=_("Is Vendor"))
    hashed_verification_code = models.CharField(max_length=200, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    block = models.BooleanField(default=False)
    address = models.OneToOneField(Address, on_delete=models.CASCADE, null=True, blank=True, default=None)
    profile_image = models.ImageField(upload_to="user_images/", null=True, blank=True)
    date_joined = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(auto_now=True)
   


    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"] 

     # Add related_name to avoid clashes
    groups = models.ManyToManyField(
        "auth.Group",
        blank=True,
        related_name="user_groups",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        blank=True,
        related_name="user_permissions",
    )

    # Override the save method to normalize the phone number before saving it
    def save(self, *args, **kwargs):
        # Parse the phone number to extract its components
        parsed_number = parse(self.phone_number, None)
        # Reformat the phone number to include a plus sign and the country code, followed by the national number
        self.phone_number = f"+{parsed_number.country_code}{parsed_number.national_number}"
        # Call the save method of the parent class (AbstractUser) to save the custom user instance
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


# Define location model
class Location(models.Model):
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    restaurant = models.ForeignKey("Restaurant", on_delete=models.CASCADE, related_name="Restaurant_locations", default=None)
    point = models.PointField(blank=True, null=True)

    
    class Meta:
        unique_together = ["street", "city", "state", "latitude", "longitude", "restaurant"]

    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


# Define restaurant model
class Restaurant(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField() 
    phone_number = models.CharField(max_length=15, unique=True,  null=True, blank=True)
    email = models.EmailField(unique=True) 
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="restaurant_location", null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="restaurants", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    opening_hours = models.TimeField(default="07:00")
    closing_hours = models.TimeField(default="21:00")
    days_of_operation = models.CharField(max_length=100, default="monday to sunday")
    logo = models.ImageField(upload_to="restaurant_images/", null=True, blank=True)
    date_created = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)
    block = models.BooleanField(default=False) 


    def save(self, *args, **kwargs):
        if self.phone_number:
            # Parse the phone number to extract its components
            parsed_number = parse(self.phone_number, None)
            # Reformat the phone number to include a plus sign and the country code, followed by the national number
            self.phone_number = f"+{parsed_number.country_code}{parsed_number.national_number}"
        
        # Call the save method of the parent class to save the custom instance
        super().save(*args, **kwargs)


# Define Category model
class Category(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    

# Define MenuItem model
class Menu(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to="item_images/", null=True, blank=True)
    deleted = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)


# Define status model
class Status(models.Model):
    name = models.CharField(max_length=50, unique=True)


# Define Order model
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    item = models.ForeignKey(Menu, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    status = models.ForeignKey(Status, on_delete=models.CASCADE, default=1)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    order_date = models.DateTimeField(auto_now=True)
    delivered = models.BooleanField(default=False)
    paid_for = models.BooleanField(default=False)
    cancel = models.BooleanField(default=False)


# Define Cart model
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    item = models.ForeignKey(Menu, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now=True)
    

    
    


    