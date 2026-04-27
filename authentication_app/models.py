from django.db import models
from quantumways.models import TimestampModel
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
import uuid
from quantumways.constants import Role
from cloudinary_storage.storage import MediaCloudinaryStorage

class UserManager(BaseUserManager):
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser, TimestampModel):
    username = None # Remove the username field
    last_login = None # Remove the last login
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField(unique=True)
    is_user_active = models.BooleanField(default=False)
    last_active = models.DateTimeField(blank=True, null=True)
    USERNAME_FIELD = 'email' # Set email as the unique identifier
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

class UserRole(TimestampModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_role')
    role = models.CharField(max_length=50, choices=Role.CHOICES)

    def __str__(self):
        return f"{self.user.email} | {self.role}"

class UserProfile(TimestampModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile')
    picture = models.ImageField(storage=MediaCloudinaryStorage(), upload_to='upload/profile_picture/', max_length=500)

    def __str__(self):
        return self.user.email
    
class UserInformation(TimestampModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_information')
    contact_number = models.CharField(max_length=11, null=True)
    address = models.CharField(max_length=255, null=True)
    birth_date = models.DateField(null=True)

    def __str__(self):
        return self.user.email
    
class UserEmergencyInformation(TimestampModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_emergency_information')
    name = models.CharField(max_length=100, blank=True, null=True)
    contact_number = models.CharField(max_length=11, blank=True, null=True)

    def __str__(self):
        return self.user.email