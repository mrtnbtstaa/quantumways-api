from rest_framework import generics, mixins, status
from rest_framework.parsers import MultiPartParser
from quantumways.permissions import HasFeatureAccess
from rest_framework.permissions import IsAuthenticated
from quantumways.utils import response_message_utils, extract_first_error_message

class BaseImportView(mixins.CreateModelMixin, generics.GenericAPIView):

    feature_name = None # Name of the feature for permission checking (used with custom permissions)

    serializer_class = None # Serializer class used when creating a new instance (POST requests)

    parser_classes = [MultiPartParser]

    permission_classes = [IsAuthenticated, HasFeatureAccess] # List of permission classes that control access to this view
    
    queryset = None

    def post(self, request, *args, **kwargs):

        try:

            if 'multipart/form-data' in self.request.content_type:

                serializer = self.get_serializer(data=request.data)

                if serializer.is_valid():
                    self.perform_create(serializer)
                    return response_message_utils(
                        message="Successfully imported the excel",
                        status_code=status.HTTP_200_OK
                    )
                
                return response_message_utils(
                    message=extract_first_error_message(serializer.errors),
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            else:
                return response_message_utils(
                    message="Unsupported content type",
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
                )

        except Exception as e:
            return response_message_utils(
                message=f"Something went wrong while importing your excel {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
