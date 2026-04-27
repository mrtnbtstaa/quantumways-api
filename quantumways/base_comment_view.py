from rest_framework import generics, mixins, status
from quantumways.utils import extract_first_error_message, response_message_utils
from rest_framework.permissions import IsAuthenticated
from django.contrib.contenttypes.models import ContentType
from comment_app.models import Comment
from django.shortcuts import get_object_or_404
from django.http import Http404
class BaseCommentView(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    generics.GenericAPIView
):
    
    permission_classes = [IsAuthenticated]

    lookup_url_kwarg = 'comment_id'

    lookup_field = 'id'

    model = None

    many = False

    create_serializer_class = None # Serializer class used when creating a new instance (POST requests)

    list_serializer_class = None # Serializer class used when listing multiple instances (GET list)

    update_serializer_class = None # Serializer class used when updating an instance (PUT/PATCH requests)


    def get_base_object(self):
        object_id = self.kwargs.get("object_id")
        return get_object_or_404(self.model, id=object_id)

    def get_serializer_class(self):

        if self.request.method == "POST":
            return self.create_serializer_class
        if self.request.method == "GET":
            return self.list_serializer_class
        if self.request.method in ("PUT", "PATCH"):
            return self.update_serializer_class
    
    def base_get_queryset(self):
        return self.model.objects

    def get_queryset(self):

        base_obj = self.get_base_object()
        content_type = ContentType.objects.get_for_model(self.model)

        if self.request.method == "GET":
            return Comment.objects.filter(content_type=content_type, object_id=base_obj.id).order_by('created_at')
        
        if self.request.method == "DELETE":
            return Comment.objects.filter(content_type=content_type, object_id=base_obj.id)
            
    def get_object(self):
        base_obj = self.get_base_object()  # (e.g,. Purchase Request, Purchase Order)
        comment_id = self.kwargs.get(self.lookup_url_kwarg)
        content_type = ContentType.objects.get_for_model(self.model)

        return get_object_or_404(
            Comment,
            id=comment_id,
            content_type=content_type,
            object_id=base_obj.id
        )

    def post(self, request, *args, **kwargs):

        try:
            
            base_obj = self.get_base_object()

            serializer = self.get_serializer(
                data=request.data,
                context={
                    'request': request,
                    'content_type': ContentType.objects.get_for_model(self.model),
                    'object_id': base_obj.id
                }
            )

            if serializer.is_valid():
                self.perform_create(serializer)

                return response_message_utils(
                    message="Successfully created comment",
                    status_code=status.HTTP_201_CREATED
                )
            
            return response_message_utils(
                message=extract_first_error_message(serializer.errors),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Http404:
            return response_message_utils(
                message="No object id found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return response_message_utils(
                message=f"Something went wrong while processing your requests {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    def get(self, request, *args, **kwargs):

        try:
            
            serializer = self.list(self.get_queryset())

            return response_message_utils(
                message="List of comments",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            return response_message_utils(
                message=f"qweqwe Something went wrong while processing your requests {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    def put(self, request, *args, **kwargs):

        try:
            instance = self.get_object()

            serializer = self.get_serializer(instance=instance, data=request.data)

            if serializer.is_valid():
                self.perform_update(serializer)

                return response_message_utils(
                    message="Successfully updated comment",
                    data=serializer.data,
                    status_code=status.HTTP_200_OK
                )
            
            return response_message_utils(
                message=extract_first_error_message(serializer.errors),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Http404:
            return response_message_utils(
                message="No comment found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return response_message_utils(
                message="Something went wrong while processing your requests",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    def patch(self, request, *args, **kawrgs):

        try:
            
            instance = self.get_object()

            serializer = self.get_serializer(instance=instance, data=request.data, partial=True)

            if serializer.is_valid():
                self.perform_update(serializer)

                return response_message_utils(
                    message="Successfully update the comment",
                    data=serializer.data,
                    status_code=status.HTTP_200_OK
                )
            
            return response_message_utils(
                message=extract_first_error_message(serializer.errors),
                status_code=status.HTTP_400_BAD_REQUEST
            )

        except Http404:
            return response_message_utils(
                message="No comment found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return response_message_utils(
                message="Something went wrong while processing your requests",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, *args, **kawrgs):

        try:
            
            instance = self.get_object()

            instance.delete()

            return response_message_utils(
                message="Successfully delete the comment",
                status_code=status.HTTP_200_OK
            )
            
        except Http404:
            return response_message_utils(
                message="No comment found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return response_message_utils(
                message="Something went wrong while processing your requests",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )