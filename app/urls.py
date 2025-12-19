from django.urls import path
from . import views

app_name = "app"

urlpatterns = [
    path("", views.index, name="home"),
    path("category/<str:category_type>/<int:pk>/", views.category_view, name="category"),
    path("subcategory/<str:category_type>/<int:pk>/", views.subcategory_view, name="subcategory"),
    # Product detail URLs with unique prefixes
    path("product/gold/g<int:pk>/", views.product_detail, {'product_type': 'gold'}, name="product_detail_gold"),
    path("product/silver/s<int:pk>/", views.product_detail, {'product_type': 'silver'}, name="product_detail_silver"),
    path("product/imitation/i<int:pk>/", views.product_detail, {'product_type': 'imitation'}, name="product_detail_imitation"),
    # Fallback for backward compatibility
    path("product/<str:product_type>/<int:pk>/", views.product_detail, name="product_detail"),
    path("shop-all/", views.shop_all, name="shop_all"),
    path("collections/<str:collection_type>/", views.collection_view, name="collection"),
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup, name="signup"),
    path("logout/", views.logout_view, name="logout"),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("api/verify-reset-otp/", views.verify_reset_otp, name="verify_reset_otp"),
    path("api/reset-password-otp/", views.reset_password_with_otp, name="reset_password_with_otp"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("api/profile/", views.profile_api, name="profile_api"),
    path("api/profile/update/", views.update_profile, name="update_profile"),
    path("checkout/", views.checkout, name="checkout"),
    path("check-email/", views.check_email, name="check_email"),
    path("api/check-email/", views.check_email, name="check_email_api"),
    path("wishlist/", views.wishlist_view, name="wishlist"),
    path("api/wishlist/", views.wishlist_api, name="wishlist_api"),
    path("api/wishlist/status/", views.wishlist_status_api, name="wishlist_status_api"),
    path("wishlist/add/<str:product_type>/<int:pk>/", views.add_to_wishlist, name="add_to_wishlist"),
    path("wishlist/remove/<str:product_type>/<int:pk>/", views.remove_from_wishlist, name="remove_from_wishlist"),
    path("cart/", views.cart_view, name="cart"),
    path("api/cart/", views.cart_api, name="cart_api"),
    # Cart URLs with unique prefixes
    path("cart/add/gold/g<int:product_id>/", views.add_to_cart, {'product_type': 'gold'}, name="add_to_cart_gold"),
    path("cart/add/silver/s<int:product_id>/", views.add_to_cart, {'product_type': 'silver'}, name="add_to_cart_silver"),
    path("cart/add/imitation/i<int:product_id>/", views.add_to_cart, {'product_type': 'imitation'}, name="add_to_cart_imitation"),
    # Fallback for backward compatibility
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/<int:item_id>/", views.update_cart, name="update_cart"),
    path("cart/remove/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("about/", views.about_us, name="about"),
    path("contact/", views.contact, name="contact"),
    path("faqs/", views.faqs, name="faqs"),
    path("privacy-policies/", views.privacy_policies, name="privacy_policies"),
    path("terms-and-conditions/", views.terms_and_conditions, name="terms_and_conditions"),
]
