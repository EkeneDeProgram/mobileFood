from django.test import TestCase

# Create your tests here.

# permission_classes = [IsAuthenticated]

#     def put(self, request, restaurant_id):
#         user = request.user

#         if not user.deleted and not user.block:
#             if not user.is_verified:
#                 return Response({"Message": f"{user.full_name} your account has not been verified"})
            
#             if user.is_vendor:

#                 try:
#                     # Get the restaurant instance
#                     restaurant_instance = Restaurant.objects.get(id=restaurant_id)
#                 except Restaurant.DoesNotExist:
#                     return Response({"Message": "Restaurant not found"}, status=status.HTTP_404_NOT_FOUND)
                
#                 # Check if the authenticated user is the owner of the restaurant
#                 if restaurant_instance.user == user:
#                     if restaurant_instance.is_active:


#                         serializer = UpdateRestaurantDetailsSerializer(data=request.data, partial=True)
#                         if serializer.is_valid():
#                             # Update restaurant details
#                             serializer.update(restaurant_instance, serializer.validated_data)
#                             restaurant = Restaurant.objects.create(**serializer.validated_data)

#                             # Serialize the updated restaurant and return it in the response
#                             updated_restaurant_serializer = UpdateRestaurantDetailsSerializer(restaurant)
#                             return Response({"message": "Restaurant details updated successfully.", "restaurant": updated_restaurant_serializer.data},
#                                                 status=status.HTTP_200_OK)
#                         else:
#                             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#                     else:
#                         return Response({"Message": f"Your {restaurant_instance.name} has not been activated"})

#                 else:
#                     return Response({"Message": "You are not authorized to update this restaurant"}, status=status.HTTP_403_FORBIDDEN)
#             else:
#                 return Response({"Message": f"{user.full_name} You are not authorized to perform this operation"})
#         else:
#             return Response({"Message": f"{user.full_name} Your account has been blocked/deleted"})


