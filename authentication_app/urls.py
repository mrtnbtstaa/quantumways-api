from django.urls import path
from .views import (
    CustomLoginObtainPairView,
    CustomTokenRefreshView,
    LogoutView,
    UserAdminView,
    UsersChangePasswordView,
    UsersUpdateInformationInAdminView,
    ForgotPasswordView
)

urlpatterns = [

    # Auth
    path('v1/login/', CustomLoginObtainPairView.as_view(), name='login'),
    path('v1/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('v1/logout/', LogoutView.as_view(), name='logout'),

    # Forgot Password
    path('v1/password-reset/', ForgotPasswordView.as_view(), name='users_forgot_password'),

    # List users, Create User, Bulk Operations
    path('v1/users/', UserAdminView.as_view(), name='list_create_users'),
    
    # Retrieve, Update, Delete
    path('v1/users/<str:user_id>/', UserAdminView.as_view(), name='retrieve_destroy_users'),

    # Change password
    path('v1/users/<str:user_id>/change-password/', UsersChangePasswordView.as_view(), name='users_change_password'),

    # Update personal information
    path('v1/users/<str:user_id>/update-information/', UsersUpdateInformationInAdminView.as_view(), name='users_update_information_details')

]