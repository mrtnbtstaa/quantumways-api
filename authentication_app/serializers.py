from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenRefreshSerializer, TokenObtainPairSerializer
from .models import User, UserRole, UserInformation, UserProfile, UserEmergencyInformation
from rest_framework_simplejwt.tokens import TokenError, OutstandingToken, BlacklistedToken, RefreshToken, AccessToken
from django.contrib.auth.hashers import check_password
from django.contrib.auth import login, authenticate
from datetime import datetime
from django.utils import timezone
from django.utils.timezone import make_aware, is_naive
from rest_framework.exceptions import PermissionDenied
from quantumways.create_activity_log import create_activity_log
from django.db import transaction
from quantumways.constants import Role
from quantumways.utils import (
    CustomCharField,
    raise_validation,
    is_valid_email,
    is_valid_password,
    is_field_empty,
    generate_password,
    send_password_to_email,
    is_valid_contact_number,
    is_valid_input_str
)

class CustomTokenRefreshSerializer(TokenRefreshSerializer):

    refresh = CustomCharField(
        blank_message="Refresh token cannot be blank",
        required_message="Refresh token is required"
    )

    def validate(self, attrs):

        try:

            refresh_token = attrs.get('refresh')

            if is_field_empty(refresh_token):
                raise_validation("Refresh token is required")

            data = super().validate(attrs)

            return {
                "access_token": data["access"],
                "refresh_token": refresh_token
            }

        except TokenError as e:
            raise_validation("Token has expired or invalid")

class CustomLoginObtainPairSerializer(TokenObtainPairSerializer):

  
    def validate(self, attrs):
        
        # Get the request object from the serializer context
        request = self.context.get('request')

        # User input fields
        email = attrs.get('email')
        password = attrs.get('password')

        if is_field_empty(email):
            raise_validation("Email cannot be blank")

        if is_field_empty(password):
            raise_validation("Password cannot be blank")

        user = authenticate(request, email=email, password=password)

        if user is None:
            raise_validation("Invalid credentials")

        allowed_roles = Role.ROLES

        user_role = getattr(getattr(user, 'user_role', None), 'role', None)

        if user_role not in allowed_roles:
            raise PermissionDenied({"message": "You do not have permission to access this page"})

        login(request, user)

        user.is_user_active = True
        user.save()

        token = self.get_token(user)
        
        return {
            "access_token": str(token.access_token),
            "refresh_token": str(token),
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user_role,
            "profile_image": (
                getattr(getattr(user, 'user_profile'), 'picture', None).url
                if getattr(getattr(user, 'user_profile'), 'picture', None)
                else None
            )
        }
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['email'] = user.email

        return token
    

class LogoutSerializer(serializers.Serializer):

    refresh = CustomCharField(
        blank_message="Refresh token cannot be blank",
        required_message="Refresh token is required"
    )

    def validate(self, attrs):

        self.refresh_token = attrs['refresh']

        # Get the request object from the serializer context
        request = self.context.get('request')

        # Get the authorization from the header
        auth_header = request.headers.get('Authorization')
        
        # Check if the 'Authorization' header is missing or doesn't start with Bearer
        if not auth_header or not auth_header.startswith('Bearer '):
            raise serializers.ValidationError({"message": 'No valid Authorization header found.'})   
        
        # Get the token part
        self.access_token_str = auth_header.split(' ')[1]

        return attrs
    
    def save(self, **kwargs):

        try:
            # Blacklist the refresh token
            refresh_token = RefreshToken(self.refresh_token)
            refresh_token.blacklist()
        except TokenError:
            raise_validation("Invalid refresh token")
            

        try:

            # Parse the token
            access_token = AccessToken(self.access_token_str)

            # Retrieve specific user with the given access token payloads
            try:
                user = User.objects.get(id=access_token["user_id"])
                user.last_active = timezone.now()
                user.is_user_active = False
                user.save()
            except User.DoesNotExist:
                raise_validation("No user found")

            # Format datetime fields
            created_at = datetime.fromtimestamp(access_token['iat'])
            expires_at = datetime.fromtimestamp(access_token['exp'])

            if is_naive(created_at):
                created_at = make_aware(created_at)

            if is_naive(expires_at):
                expires_at = make_aware(expires_at)

            # Create OutstandingToken if not exists, if exists return the existing 
            outstanding_token, _ = OutstandingToken.objects.get_or_create(
                jti=access_token["jti"],
                defaults={
                    "user_id": self.context['request'].user.id,
                    "token": str(access_token),
                    "created_at": created_at.isoformat(),
                    "expires_at": expires_at.isoformat()
                }
            )

            # Blacklist the token
            BlacklistedToken.objects.get_or_create(token=outstanding_token)

        except TokenError as e:
            raise_validation("Invalid access token")
        except Exception as e:
            raise_validation("Error occured during logout")


class AddAccountAndViewInAdminSerializer(serializers.Serializer):

    role = CustomCharField(
        blank_message="Role cannot be blank",
        required_message="Role is required",
    )
    firstname = CustomCharField(
        blank_message="Firstname cannot be blank",
        required_message="Firstname is required",
    )
    lastname = CustomCharField(
        blank_message="Lastname cannot be blank",
        required_message="Lastname is required",
    )
    contact_number = CustomCharField(
        blank_message="Contact number cannot be blank",
        required_message="Contact number is required",
    )
    email = CustomCharField(
        blank_message="Email cannot be blank",
        required_message="Email is required",
    )
    address = CustomCharField(
        blank_message="Address cannot be blank",
        required_message="Address is required",
    )
    birth_date = serializers.DateField(input_formats=['%m/%d/%Y'])
    picture = serializers.ImageField(required=False)

    def to_internal_value(self, data):
        if data["birth_date"] in (None, "") or data["birth_date"].strip() == "":
            raise_validation("Birth date cannot be blank")
        return super().to_internal_value(data)

    def validate(self, attrs):
        
        allowed_roles = Role.ROLES

        # Input validations
        if 'picture' not in attrs or is_field_empty(attrs["picture"]):
            raise_validation("Picture cannot be blank")

        if is_field_empty(attrs["role"]):
            raise_validation("Role cannot be blank")

        if attrs["role"] not in allowed_roles:
            raise_validation("Invalid role")
        
        if is_field_empty(attrs["firstname"]):
            raise_validation("Firstname cannot be blank")

        if not is_valid_input_str(attrs["firstname"]):
            raise_validation("Firstname should not contain numbers or special characters")

        if is_field_empty(attrs["lastname"]):
            raise_validation("Lastname cannot be blank")

        if not is_valid_input_str(attrs["lastname"]):
            raise_validation("Lastname should not contain numbers or special characters")
        
        if is_field_empty(attrs["contact_number"]):
            raise_validation("Contact number cannot be blank")

        if not is_valid_contact_number(attrs["contact_number"]):
            raise_validation("Contact number must only contain digits")

        if len(attrs["contact_number"]) > 11:
            raise_validation("Contact number must not exceed 11 digits")

        if is_field_empty(attrs["email"]):
            raise_validation("Email cannot be blank")

        if not is_valid_email(attrs["email"]):
            raise_validation("The email you entered is invalid")

        if is_field_empty(attrs["address"]):
            raise_validation("Address cannot be blank")
            
        if User.objects.filter(email=attrs["email"]).exists():
            raise_validation("user with this email already exists")

        return attrs

    def create(self, validated_data):
        try:
            # Add transaction atomic to ensure rollback incase any of failure
            with transaction.atomic():
                
                # Call the generate password to generate random passwords
                password = generate_password()

                # Create user
                user = User.objects.create_user(
                    email=validated_data["email"],
                    password=password,
                    first_name=validated_data["firstname"],
                    last_name=validated_data["lastname"]
                )

                # Create user role
                user_role = UserRole.objects.create(
                    user=user,
                    role=validated_data['role']
                )

                # Create User information
                user_information = UserInformation.objects.create(
                    user=user,
                    contact_number=validated_data["contact_number"],
                    address=validated_data["address"],
                    birth_date=validated_data["birth_date"]
                )

                # Create User profile
                user_profile = UserProfile.objects.create(
                    user=user,
                    picture=validated_data.get('picture', None)
                )   

                send_password_to_email(
                    subject="Your Account Password",
                    message="Your account has been successfully created. You can now log in using the credentials below:",
                    recipient_list=[user.email],
                    generated_password=password,
                )

                return user
        except Exception as e:
            raise_validation(f"Something went wrong when creating an account: {e}")

            
class UsersListSerializer(serializers.Serializer):

    id = serializers.CharField()
    email = serializers.CharField()
    firstname = serializers.CharField(source='first_name')
    lastname = serializers.CharField(source='last_name')
    role = serializers.CharField(source='user_role__role')
    is_active = serializers.BooleanField(source='is_user_active')
    date_created = serializers.DateTimeField(source='date_joined')
    last_active = serializers.DateTimeField()

    def to_representation(self, instance):

        # Get the request object from the serializer context
        request = self.context.get('request')

        data = super().to_representation(instance)

        user_profile = UserProfile.objects.get(user_id=instance.get('id'))

        picture = None

        if user_profile and user_profile.picture:
            picture = request.build_absolute_uri(user_profile.picture.url)
        else:
            picture = None
        

        data["profile_image"] = picture

        return data
    

class SearchUsersListSerializer(serializers.ModelSerializer):

    firstname = serializers.CharField(source='first_name')
    lastname = serializers.CharField(source='last_name')
    role = serializers.CharField(source='user_role.role')
    is_active = serializers.BooleanField(source='is_user_active')
    date_created = serializers.DateTimeField(source='date_joined')
    profile_image = serializers.ImageField(source='user_profile.picture')

    class Meta:
        model = User
        fields = ['id', 'email', 'firstname', 'lastname', 'role', 'is_active', 'date_created', 'last_active', 'profile_image']

class UsersDetailsSerializer(serializers.Serializer):

    id = serializers.CharField()
    email = serializers.CharField()
    firstname = serializers.CharField(source='first_name')
    lastname = serializers.CharField(source='last_name')
    role = serializers.CharField(source='user_role__role')
    # picture = serializers.ImageField(source='user_profile__picture')
    # is_active = serializers.BooleanField(source='is_user_active')
    # date_created = serializers.DateTimeField(source='date_joined')
    # last_active = serializers.DateTimeField()

    def to_representation(self, instance):

        # Get the request object from the serializer context
        request = self.context.get('request')
        data = super().to_representation(instance)

        picture = None

        try:
            user_profile = UserProfile.objects.get(user_id=instance.get('id'))
            picture = request.build_absolute_uri(user_profile.picture.url)
        except UserProfile.DoesNotExist:
            picture = None

        try:
            user_information = UserInformation.objects.get(user=instance.get('id'))
            data["address"] = user_information.address
            data["contact_number"] = user_information.contact_number
            data["birthdate"] = user_information.birth_date
        except UserInformation.DoesNotExist:
            data["address"] = None
            data["contact_number"] = None
            data["birthdate"] = None
        
 
        
        data["profile_image"] = picture

        try:
            emergency_information = UserEmergencyInformation.objects.get(user=instance.get('id'))
            data["emergency_information"] = {
                "contact_number": emergency_information.contact_number,
                "name": emergency_information.name,
            }
        except UserEmergencyInformation.DoesNotExist:
            data["emergency_information"] = {
                "contact_number": None,
                "name": None,
            }

        return data


class UsersChangePasswordSerializer(serializers.Serializer):

    old_password = CustomCharField(
        blank_message="Old password cannot be blank",
        required_message="Old password is required"
    )
    new_password = CustomCharField(
        blank_message="New password cannot be blank",
        required_message="New password is required"
    )
    confirm_password = CustomCharField(
        blank_message="Confirm password cannot be blank",
        required_message="Confirm password is required"
    )

    def validate(self, attrs):
        
        # Get the user_id from the serializer context
        user_id = self.context.get('user_id')

        old_password = attrs.get('old_password')
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise_validation("No user found")

        if is_field_empty(old_password):
            raise_validation("Old password cannot be blank")

        if old_password and not check_password(old_password, user.password):
            raise_validation("Old password do not match")

        if is_field_empty(new_password):
            raise_validation("New password cannot be blank")

        if is_field_empty(confirm_password):
            raise_validation('Confirm password cannot be blank')

        if len(new_password) < 8 or len(confirm_password) < 8:
            raise_validation("Password must be atleast 8 characters")

        if not is_valid_password(new_password) or not is_valid_password(confirm_password):
            raise_validation("Password must include at least one uppercase letter, one lowercase letter, one number, and one special character")

        if new_password != confirm_password:
            raise_validation("New password and confirm password do not match")

        if new_password and check_password(new_password, user.password):
            raise_validation("New password cant be the same to the old password")

        self.instance = user

        return attrs

    
    def update(self, instance, validated_data):
        
        validated_data.pop('old_password')
        validated_data.pop('confirm_password')

        instance.set_password(validated_data.get('new_password', None))

        instance.save()

        return instance


class UsersViewInformationInAdminSerializer(serializers.Serializer):

    id = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.CharField()
    contact_number = serializers.CharField(source='user_information__contact_number')
    address = serializers.CharField(source='user_information__address')
    name = serializers.CharField(source='user_emergency_information__name')
    emergency_contact_number = serializers.CharField(source='user_emergency_information__contact_number')

    def to_representation(self, instance):
        
        # Get the request object from the serializer context
        request = self.context.get('request')

        data = super().to_representation(instance)

        user_profile = UserProfile.objects.get(user_id=instance.get('id'))

        picture = None

        if user_profile and user_profile.picture:
            picture = user_profile.picture.url
        else:
            picture = None

        data["profile_image"] = request.build_absolute_uri(picture)

        data["emergency_info"] = {
            "name": data.pop('name'),
            "contact_number": data.pop('emergency_contact_number')
        }

        return data

class UsersUpdateInformationInAdminSerializer(serializers.Serializer):

    first_name = CustomCharField(
        blank_message="Firstname cannot be blank",
        required_message="Firstname is required",
    )
    last_name = CustomCharField(
        blank_message="Lastname cannot be blank",
        required_message="Lastname is required"
    )
    email = CustomCharField(
        blank_message="Email cannot be blank",
        required_message="Email is required"
    )
    role = CustomCharField(
        blank_message="Role cannot be blank",
        required_message="Role is required"
    )
    contact_number = CustomCharField(
        blank_message="Contact number cannot be blank",
        required_message="Contact number is required",
    )
    address = CustomCharField(
        blank_message="Address cannot be blank",
        required_message="Address is required",
    )
    picture = serializers.ImageField(
        required=False,
    )
    emergency_name = CustomCharField(
        None,
        None,
        required=False,
        allow_blank=True
    )
    emergency_contact_number = CustomCharField(
        None,
        None,
        required=False,
        allow_blank=True
    )
    
    def validate(self, attrs):

        if is_field_empty(attrs["first_name"]):
            raise_validation("Firstname cannot be blank")

        if not is_valid_input_str(attrs["first_name"]):
            raise_validation("Firstname should not contain numbers or special characters")

        if is_field_empty(attrs["last_name"]):
            raise_validation("Lastname cannot be blank")

        if not is_valid_input_str(attrs["last_name"]):
            raise_validation("Lastname should not contain numbers or special characters")

        if is_field_empty(attrs["email"]):
            raise_validation("Email cannot be blank")

        if not is_valid_email(attrs["email"]):
            raise_validation("The email you entered is invalid")

        if is_field_empty(attrs["role"]):
            raise_validation("Role cannot be blank")

        allowed_roles = Role.ROLES

        if attrs["role"] not in allowed_roles:
            raise_validation("Invalid role")
            
        if is_field_empty(attrs["contact_number"]):
            raise_validation("Contact number cannot be blank")

        if not is_valid_contact_number(attrs["contact_number"]):
            raise_validation("Contact number must only contain digits")

        if len(attrs["contact_number"]) > 11:
            raise_validation("Contact number must not exceed 11 digits")

        if is_field_empty(attrs.get('address')):
            raise_validation("Address cannot be blank")

        if is_field_empty(attrs.get('picture')):
            raise_validation("Picture cannot be blank")

        if not is_valid_input_str(attrs["emergency_name"]):
            raise_validation("Name should not contain numbers or special characters")

        if not is_valid_contact_number(attrs["emergency_contact_number"]):
            raise_validation("Contact number must only contain digits")

        if len(attrs["emergency_contact_number"]) > 11:
            raise_validation("Contact number must not exceed 11 digits")

        return attrs
    
    def update(self, instance, validated_data):

        request = self.context.get('request')

        try:
            with transaction.atomic():

                instance.first_name = validated_data.get('first_name', instance.first_name)
                instance.last_name = validated_data.get('last_name', instance.last_name)
                instance.email = validated_data.get('email', instance.email)
                instance.save()

                # Update of user profile
                UserProfile.objects.filter(user=instance).update(
                    picture=validated_data.get('picture', None)
                )

                # Get the current value of the role
                current_role = getattr(getattr(instance, 'user_role', None), 'role', None)

                # Create an activity log only if the current database role value has changed
                if current_role != validated_data["role"]:
                    create_activity_log(
                        request=request,
                        activity_type="Role Update",
                        content_object=instance,
                        unique_no=None,
                        changes=f"User Role Changed: {current_role} to {validated_data["role"]}"
                    )

                    UserRole.objects.filter(user=instance).update(
                        role=validated_data["role"]
                    )

  

                # Update of user information
                UserInformation.objects.filter(user=instance).update(
                    contact_number=validated_data.get('contact_number'),
                    address=validated_data.get('address')
                )

                # Update of user emergency information
                UserEmergencyInformation.objects.update_or_create(
                    user=instance,
                    defaults={
                        "name": validated_data.get('emergency_name', None),
                        "contact_number": validated_data.get('emergency_contact_number', None)
                    }
                )

                return instance
            

        except Exception as e:
            raise_validation(e)



class ForgotPasswordSerializer(serializers.Serializer):

    email = CustomCharField(
        blank_message="Email cannot be blank",
        required_message="Email is required"
    )

    def validate_email(self, value):

        if is_field_empty(value):
            raise_validation("Email cannot be blank")

        if not User.objects.filter(email=value).exists():
            raise_validation("No user found")

        return value
    
    def update(self, instance, validated_data):
        
        # Generate password
        password = generate_password()

        # Set the new password
        instance.set_password(password)

        # Save the new password
        instance.save()

        # Send mail
        send_password_to_email(
            subject="Your Account Password",
            message="Your account password has been successfully reset. You can now log in using the credentials below:",
            recipient_list=[instance],
            generated_password=password,
        )

        return instance
    




    