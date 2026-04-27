from .serializers import AssignUserFeaturePermissionsSerializer, AssignedPermissionDetailsSerializer
from rest_framework import generics, mixins, status
from rest_framework.permissions import IsAuthenticated
from .models import UserFeaturePermission, Feature
from quantumways.utils import response_message_utils
from authentication_app.models import User

class AssignUserBasedPermissionsView(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    generics.GenericAPIView
):
    
    permission_classes = [IsAuthenticated]
    queryset = Feature.objects.all()
    lookup_url_kwarg = 'user_id'
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.request.method == "GET":
            if self.kwargs.get(self.lookup_url_kwarg):
                return AssignedPermissionDetailsSerializer
        return AssignUserFeaturePermissionsSerializer
    

    def get_queryset(self):

        user_id = self.kwargs.get('user_id')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return response_message_utils(
                message="No user found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        return UserFeaturePermission.objects.filter(user=user)

    def post(self, request, *args, **kwargs):

        try:

            user_id = kwargs.get('user_id')

            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return response_message_utils(
                    message="No user found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            serializer = self.get_serializer(data=request.data, context={'user': user})


            if serializer.is_valid():
                self.perform_create(serializer)

                return response_message_utils(
                    message="Successfully assigned permission",
                    status_code=status.HTTP_201_CREATED
                )
            
            return response_message_utils(
                message=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return response_message_utils(
                message=f"Something went wrong while processing your requests: {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    def get(self, request, *args, **kwargs):

        try:
            
            
            queryset = self.get_queryset()


            serializer = self.get_serializer(queryset, many=True)

            return response_message_utils(
                message="Assigned Permissions",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            return response_message_utils(
                message="Something went wrong while processing your requests",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    