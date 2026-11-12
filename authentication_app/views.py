from quantumways.utils import response_message_utils, extract_first_error_message
from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from authentication_app.models import User
from rest_framework import generics, status, mixins
from django_filters import rest_framework as filters
from quantumways.throttling.token_bucket_throttle import TokenBucketThrottle
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from quantumways.constants import Role
from quantumways.pagination.main_pagination import CustomPageNumberPagination
from rest_framework.permissions import IsAuthenticated
from django.db.models.functions import Concat, Coalesce
from django.db.models import Value, CharField
from quantumways.filter import UserFilter
from rest_framework.permissions import AllowAny
from django.db.models import Q

from .serializers import (
    CustomLoginObtainPairSerializer,
    LogoutSerializer,
    CustomTokenRefreshSerializer,
    AddAccountAndViewInAdminSerializer,
    UsersListSerializer,
    SearchUsersListSerializer,
    UsersDetailsSerializer,
    UsersChangePasswordSerializer,
    UsersUpdateInformationInAdminSerializer,
    UsersViewInformationInAdminSerializer,
    ForgotPasswordSerializer
)

class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer

    def post(self, request, *args, **kwargs):

        try:

            serializer = self.get_serializer(data=request.data)

            if serializer.is_valid():
                return response_message_utils(
                    message="Successfully refresh your token",
                    data=serializer.validated_data,
                    status_code=status.HTTP_200_OK
                )
            
            return response_message_utils(
                message=extract_first_error_message(serializer.errors),
                status_code=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return response_message_utils(
                message="Something went wrong while processing your request",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CustomLoginObtainPairView(TokenObtainPairView):
    
    serializer_class = CustomLoginObtainPairSerializer

    def post(self, request, *args, **kwargs):

        try:

            serializer = self.get_serializer(data=request.data, context={'request': request})

            if serializer.is_valid():
                return response_message_utils(
                    message="Successfully logged in",
                    data=serializer.validated_data,
                    status_code=status.HTTP_200_OK
                )
            
            return response_message_utils(
                message=extract_first_error_message(serializer.errors),
                status_code=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return response_message_utils(
                message=f"Something went wrong while processing your request {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class LogoutView(generics.CreateAPIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()

    def post(self, request, *args, **kwargs):

        try:
            
            serializer = self.get_serializer(data=request.data, context={'request': request})

            if serializer.is_valid():
                serializer.save()
                return response_message_utils(
                    message="Successfully logged out",
                    status_code=status.HTTP_200_OK
                )
            
            return response_message_utils(
                message=extract_first_error_message(serializer.errors),
                status_code=status.HTTP_400_BAD_REQUEST
            )

        except ValidationError as e:
            return response_message_utils(
                message=extract_first_error_message(e.detail),
                status_code=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return response_message_utils(
                message="Something went wrong while processing your request",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserAdminView(
    mixins.ListModelMixin,
    generics.GenericAPIView
):

    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination
    lookup_field = 'id' 
    lookup_url_kwarg = 'user_id' # Capture the url query param(user_id)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = UserFilter

    def get_throttles(self):
        # Apply the custom rate limiting only for POST request using the TokenBucketThrottle
        if self.request.method == "POST":
            return [TokenBucketThrottle()]
        return super().get_throttles()
    
    def get_base_queryset(self):
        return User.objects.select_related(
            'user_role',
            'user_profile',
            'user_information'
        ).filter(user_role__role__in=Role.ROLES).annotate(
            full_name=Concat(
                Coalesce('first_name', Value(' ')),
                Value(' '),
                Coalesce('last_name', Value(' ')),
                output_field=CharField()
            )
        )

    def get_queryset(self):

        base_queryset = self.get_base_queryset()

        if self.request.method == "GET":

    
            if self.kwargs.get(self.lookup_url_kwarg):

                return base_queryset.filter(id=self.kwargs["user_id"]).values(
                    'id', 'first_name', 'last_name',
                    'user_role__role', 'user_profile__picture',
                    'user_information__contact_number',
                    'user_information__address',
                    'is_user_active', 'email', 'date_joined', 'last_active'
                )
            
            else:

                search = self.request.query_params.get('search')

                if search:
                    return base_queryset.filter(
                        Q(first_name__icontains=search) |
                        Q(last_name__icontains=search)
                    )
                else:
                    return base_queryset.values(
                        'id', 'first_name', 'last_name',
                        'user_role__role', 'user_profile__picture',
                        'user_information__contact_number',
                        'user_information__address',
                        'is_user_active', 'email', 'date_joined', 'last_active'
                    ).order_by('created_at')
               
    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddAccountAndViewInAdminSerializer
        if self.request.method == "GET":
            if self.request.query_params.get('search'):
                return SearchUsersListSerializer
            if self.kwargs.get(self.lookup_url_kwarg) is None:
                return UsersListSerializer
            else:
                return UsersDetailsSerializer

    def get(self, request, *args, **kwargs):

        try:
            
            # If query param user_id exists retrieve single user
            if kwargs.get("user_id"):

                user = self.get_queryset().first()

                if not user:
                    return response_message_utils(
                        message="No user(s) id found",
                        status_code=status.HTTP_404_NOT_FOUND
                    )
                
                serializer = self.get_serializer(user, many=False, context={'request': request})

                return response_message_utils(
                    message="Successfully found a user qweqwewq",
                    data=serializer.data,
                    status_code=status.HTTP_200_OK
                )
            
            else: 
 
                search = request.query_params.get('search')

                if search is None:

                    serializer = self.list(self.get_queryset())

                    return response_message_utils(
                        message="List of users",
                        data=serializer.data,
                        status_code=status.HTTP_200_OK
                    )
                
                else:

                    if not self.get_queryset().exists():
                        return response_message_utils(
                            message="No users found",
                            status_code=status.HTTP_404_NOT_FOUND
                        )
                    
                    serializer = self.list(self.get_queryset())

                    return response_message_utils(
                        message="Successfully found users",
                        data=serializer.data,
                        status_code=status.HTTP_200_OK
                    )
                
        except Exception as e:
            return response_message_utils(
                message=f"Something went wrong while processing your request {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, *args, **kwargs):

        try:

            serializer = self.get_serializer(data=request.data, context={'request': request})

            if serializer.is_valid():
                serializer.save()
                return response_message_utils(
                    message="Successfully added an account",
                    status_code=status.HTTP_201_CREATED
                )
            
            return response_message_utils(
                message=extract_first_error_message(serializer.errors),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:
            return response_message_utils(
                message="Something went wrong while processing your request",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, *args, **kwargs):

        try:

            queryset = (
                User.objects
                .select_related('user_role')
                .filter(user_role__role__in=Role.ROLES)
            )

            user_ids = request.data.get('user_ids')

            if user_ids:

                if not isinstance(user_ids, list) or len(user_ids) < 1:
                    return response_message_utils(
                        message="user_ids must be a non-empty list",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                
                users_to_delete = queryset.filter(id__in=user_ids)

                if users_to_delete.count() != len(user_ids):
                    return response_message_utils(
                        message="No user(s) id found",
                        status_code=status.HTTP_404_NOT_FOUND
                    )
                    
                
                users_to_delete.delete()

                return response_message_utils(
                    message=f"Successfully deleted user(s)",
                    status_code=status.HTTP_200_OK
                )

            user_id = kwargs.get('user_id')

            if user_id:

                user_to_delete = queryset.filter(id=user_id)

                if not user_to_delete.exists():
                    return response_message_utils(
                        message="No user(s) id found",
                        status_code=status.HTTP_404_NOT_FOUND
                    )
                
                user_to_delete.delete()

                return response_message_utils(
                    message="Successfully deleted user",
                    status_code=status.HTTP_200_OK
                )

            return response_message_utils(
                message="No user ID(s) provided.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return response_message_utils(
                message="Something went wrong while processing your request",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UsersChangePasswordView(generics.UpdateAPIView):

    serializer_class = UsersChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [TokenBucketThrottle]
    lookup_field = 'user_id'

    def get_queryset(self):
        return User.objects.get(id=self.kwargs.get('user_id'))

    def patch(self, request, *args, **kwargs):

        try:

            serializer = self.get_serializer(data=request.data, context={'request': request, 'user_id': kwargs.get('user_id')}, partial=True)

            if serializer.is_valid():
                serializer.save()
                return response_message_utils(
                    message="Successfully update your password",
                    status_code=status.HTTP_200_OK
                )
            
            return response_message_utils(
                message=extract_first_error_message(serializer.errors),
                status_code=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return response_message_utils(
                message="Something went wrong while processing your request",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class UsersUpdateInformationInAdminView(generics.RetrieveUpdateAPIView):

    permission_classes = [IsAuthenticated]
    lookup_field = 'user_id'

    def get_throttles(self):
        # Apply the custom rate limiting only for PATCH request using the TokenBucketThrottle
        if self.request.method == "PATCH":
            return [TokenBucketThrottle()]
        return super().get_throttles()
    
    def get_base_queryset(self):
        return (
            User.objects
            .select_related(
                'user_role',
                'user_information',
                'user_emergency_information',
                'user_profile'
            )
        )
    
    def get_queryset(self):

        base_queryset = self.get_base_queryset()

        if self.request.method == "GET":
            base_queryset = base_queryset.values(
                'id',
                'first_name',
                'last_name',
                'email',
                'user_information__contact_number',
                'user_information__address',
                'user_profile__picture',
                'user_emergency_information__name',
                'user_emergency_information__contact_number'
            ).filter(
                user_role__role__in=Role.ROLES,
                id=self.kwargs.get('user_id')
            )

        # Patch request
        return base_queryset.filter(
            user_role__role__in=Role.ROLES,
            id=self.kwargs.get('user_id')
        )
    
    def get_serializer_class(self):
        if self.request.method == "GET":
            return UsersViewInformationInAdminSerializer
        return UsersUpdateInformationInAdminSerializer
    
    def patch(self, request, *args, **kwargs):

        try:
            
            if not self.get_queryset().exists():
                return response_message_utils(
                    message="No user(s) id found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            serializer = self.get_serializer(instance=self.get_queryset().first(), data=request.data, partial=True, context={'request': request})

            if serializer.is_valid():
                user = serializer.save()
                user.refresh_from_db() # Refresh the db to get the latest update
                return response_message_utils(
                    message="Successfully update the personal information",
                    data={
                        "id": str(user.id),
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "role": getattr(getattr(user, 'user_role', None), 'role', None),
                        "contact_number": user.user_information.contact_number if user.user_information else None,
                        "address": user.user_information.address if user.user_information else None,
                        "profile_image": request.build_absolute_uri(user.user_profile.picture.url) if user.user_profile and user.user_profile.picture else None,
                        "emergency_info": {
                            "name": getattr(getattr(user, 'user_emergency_information', None), 'name', None),
                            "contact_number": getattr(getattr(user, 'user_emergency_information', None), 'contact_number', None)
                        }
                    },
                    status_code=status.HTTP_200_OK
                )
            
            # user.user_role.role.name if user.user_role and user.user.role.name else None
            
            return response_message_utils(
                message=extract_first_error_message(serializer.errors),
                status_code=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return response_message_utils(
                message=f"qwewqe qSomething went wrong while processing your request {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request, *args, **kwargs):

        try:

            user = self.get_queryset().first()

            if not user:
                return response_message_utils(
                    detail="No personal information found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            serializer = self.get_serializer(user, context={'request': request})

            return response_message_utils(
                message="User personal information found",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
        
        except User.DoesNotExist:
            return response_message_utils(
                message="No personal information found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return response_message_utils(
                message="Something went wrong while processing your request",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ForgotPasswordView(mixins.UpdateModelMixin, generics.GenericAPIView):
    authentication_classes = [] # Disable JWT for the forgot password
    serializer_class = ForgotPasswordSerializer
    throttle_classes = [TokenBucketThrottle]
    permission_classes = [AllowAny]
    
    def get_object(self):
        try:
            return User.objects.get(email=self.request.data.get('email'))
        except User.DoesNotExist:
            return response_message_utils(
                message="No email found with this email.",
                status_code=status.HTTP_404_NOT_FOUND
            )

    def patch(self, request, *args, **kwargs):

        try:

            instance = self.get_object()

            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            return response_message_utils(
                message="Successfully reset your password, Please check your email",
                status_code=status.HTTP_200_OK
            )
        
        except serializers.ValidationError as ve:
            return response_message_utils(
                message=extract_first_error_message(ve.detail),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return response_message_utils(
                message="Something went wrong while processing your request",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )