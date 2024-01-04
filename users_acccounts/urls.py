from django.urls import path
from .views import *


urlpatterns = [
    # User urls
    path("user/register_user/", RegistrationView.as_view(), name="register-user"),
    path("user/register_vendor/", RegisterVendorView.as_view(), name="register-vendor"),
    path("user/login_user/", LoginUserView.as_view(), name="login-user"),
    path("user/verify_user/", VerifyUserView.as_view(), name="verify-user"),
    path("user/resend_verification_code/", ResendVerificationCodeView.as_view(), name="resend-verification-code"),
    path("user/get_user/", GetUserView.as_view(), name="get-user"),
    path("user/update_user_email/", UpdateUserEmailView.as_view(), name="update-user-email"),
    path("user/update_user_phone_number/", UpdateUserPhoneNumberView.as_view(), name="update-user-phone-number"),
    path("user/update_user_details/", UpdateUserDetailsView.as_view(), name="update-user-phone-details"),
    path("user/update_user_address/", UpdateUserAddressView.as_view(), name="update-user-address"),
    path("user/delete_user/", DeleteUserView.as_view(), name="delete-user"),
    # Restaurant urls
    path("restaurant/create_restaurant/", RestaurantCreateView.as_view(), name="create-restaurant"),
    path("restaurant/update_restaurant_location/<int:restaurant_id>/", UpdateRestaurantLocationView.as_view(), name="update-restaurant-location"),
    path("restaurant/update_restaurant_details/<int:restaurant_id>/", UpdateRestaurantDetailsView.as_view(), name="update-restaurant-details"),
    path("restaurant/delete_restaurant/<int:restaurant_id>/", DeleteRestaurantView.as_view(), name="delete-restaurant"),
    # Menu urls
    path("menu/add_item/<int:restaurant_id>/", AddMenuItemView.as_view(), name="add-item"),
    path("menu/update_item/<int:restaurant_id>/<int:menu_item_id>/", UpdateMenuItemView.as_view(), name="update-item"),
    path("menu/delete_item/<int:restaurant_id>/<int:menu_item_id>/", DelteMenuItemView.as_view(), name="delete-item"),
    # Get restaurant urls
    path("restaurant/active_restaurants/", ActiveRestaurantsView.as_view(), name="active-restaurants"),
    path("restaurant/user_active_restaurants/", UserActiveRestaurantsView.as_view(), name="user-active-restaurants"),
    path("restaurant/restaurant_detail/<int:restaurant_id>/", RestaurantDetailView.as_view(), name="restaurant-detail"),
    # Get menu item urls
    path("menu/all_items/", AllItemsView.as_view(), name="all-items"),
    path("menu/restaurant_menu/<int:restaurant_id>/", RestaurantMenuView.as_view(), name="restaurant-menu"),
    path("menu/restaurant_items/<int:restaurant_id>/", RestaurantItemsView.as_view(), name="restaurant-items"),
    path("menu/item/<int:menu_item_id>/", ItemView.as_view(), name="item"),
    path("menu/items_by_category/<int:category_id>/", ItemsByCategoryView.as_view(), name="items-by-category"),
    # Search urls
    path("search/search_restaurants/", SearchRestaurantView.as_view(), name="search-restaurants"),
    path("search/search_items/", SearchMenuView.as_view(), name="search-items"),
    path("search/search_restaurants_by_location/", SearchRestaurantByLocationView.as_view(), name="search-restaurant-by-location"),
    # cart urls
    path("cart/add/<int:item_id>/", AddToCartView.as_view(), name="add"), 
    path("cart/update/<int:item_id>/", UpdateCartItemView.as_view(), name="update"),
    path("cart/delete/<int:item_id>/", DeleteCartItemView.as_view(), name="delete"),
    path("cart/clear/", ClearCartView.as_view(), name="clear"),
    # Get cart urls
    path("cart/user_cart/", UserCartView.as_view(), name="user_cart"),
    # Order urls
    path("order/make_order/", MakeOrderView.as_view(), name="make-order"),
    path("order/update_order/<int:order_id>/", RestaurantUpdateOrderView.as_view(), name="update-order"),
    path("order/cancel_order/<int:order_id>/", CancelOrderView.as_view(), name="cancel-order"),
    # Get order urls
    path("order/user_order/", UserOrderView.as_view(), name="user-order"),
    path("order/restaurant_order/<int:restaurant_id>/", RestaurantOrderView.as_view(), name="restaurant-order"),
    path("order/order_details/<int:order_id>/", OrderView.as_view(), name="order-view"),
]
