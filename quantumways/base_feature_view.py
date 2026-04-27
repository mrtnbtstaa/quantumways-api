from rest_framework import mixins, generics, status
from rest_framework.permissions import IsAuthenticated
from quantumways.utils import extract_first_error_message, response_message_utils
from django.shortcuts import get_object_or_404
from quantumways.throttling.token_bucket_throttle import TokenBucketThrottle
import uuid
from django.http import Http404
from django.db.models import Q
from quantumways.create_activity_log import create_activity_log
from quantumways.permissions import HasFeatureAccess
from .pagination.main_pagination import CustomPageNumberPagination

class BaseFeatureView(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView
):
   
    feature_name = None # Name of the feature for permission checking (used with custom permissions)

    permission_classes = [IsAuthenticated, HasFeatureAccess] # List of permission classes that control access to this view

    pagination_class = CustomPageNumberPagination

    lookup_field = 'slug' # Field used to retrieve an object from the database in detail views

    lookup_url_kwarg = 'slug' # The URL keyword argument that will be used to extract the lookup value from the URL

    lookup_id_field = 'id' # Field name used to uniquely identify a record when `lookup_field` is set to "id"

    lookup_no_field = None # Optional secondary lookup field, useful when looking up objects without a direct identifier


    model = None # The model associated with the view

    
    create_serializer_class = None # Serializer class used when creating a new instance (POST requests)

    list_serializer_class = None # Serializer class used when listing multiple instances (GET list)

    detail_serializer_class = None # Serializer class used when retrieving a single instance (GET detail)

    update_serializer_class = None # Serializer class used when updating an instance (PUT/PATCH requests)

    search_serializer_class = None # Serializer class used when searching/filtering objects (GET with query params 'search')

    # Custom messsages response
    success_create_message = None
    success_list_message = None
    success_detail_message = None
    success_update_message = None
    success_bulk_delete_message = None
    success_single_delete_message = None
    not_found_message = None
    not_found_search = None

    many = False

    # Custom messages for the activity logs
    created_activity_type_message = None
    created_activity_changes_message = None

    update_activity_type_message = None
    update_activity_changes_message = None

    delete_activity_type_message = None
    delete_activity_changes_message = None

    unique_control_no = None

    # Field to used when searching(search_serializer_class)
    item_to_search = None

    # Always need this for updating multiple data
    prefetch_related_model = None

    select_related_model = None

    # Only apply throttle to specific method "POST"
    def get_throttles(self):
        if self.request.method == "POST":
            return [TokenBucketThrottle()]
        return super().get_throttles()

    def base_get_queryset(self):
        return self.model.objects
    

    def get_queryset(self):

        lookup = self.kwargs.get(self.lookup_url_kwarg)

        base_qs = self.base_get_queryset()

        # Delete requests
        if self.request.method == "DELETE":

            ids_or_no = self.request.data.get('ids_or_no') # Can be ids or strings like 0002

            # Bulk delete
            if ids_or_no:
                return base_qs

            # Single delete
            if not lookup:
                raise Http404("Missing lookup for delete.")

            try:
                uuid_val = uuid.UUID(lookup)
                return base_qs.filter(**{self.lookup_id_field: uuid_val}) #
            except ValueError:
                return base_qs.filter(**{self.lookup_no_field: lookup})
        
        # Get requests(LIST)
        if self.request.method == "GET":

            search = self.request.query_params.get('search')

            if self.item_to_search and search:
                filter_kwargs = {self.item_to_search: search}
                print(f"FOUND: {base_qs.order_by('created_at').filter(**filter_kwargs)}")
                return base_qs.order_by('created_at').filter(**filter_kwargs)

            if lookup is None:
                return base_qs.order_by('created_at')
            try:
                uuid_val = uuid.UUID(lookup)
                return base_qs.filter(**{self.lookup_id_field: uuid_val}) #
            except ValueError:
                return base_qs.filter(**{self.lookup_no_field: lookup})
        
        return base_qs
    
    # For update request
    def get_object(self):
        queryset = self.model.objects

        if self.select_related_model:
            queryset = queryset.select_related(*self.select_related_model)

        if self.prefetch_related_model:
            queryset = queryset.prefetch_related(self.prefetch_related_model)

        lookup = self.kwargs.get(self.lookup_url_kwarg)

        if not lookup:
            return 

        try:
            uuid_val = uuid.UUID(lookup)
            return get_object_or_404(queryset, **{self.lookup_id_field: uuid_val})
        except ValueError:
            return get_object_or_404(
                queryset,
                **{self.lookup_no_field: lookup}
            )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return self.create_serializer_class
        if self.request.method == "PUT":
            return self.update_serializer_class
        if self.request.method == "PATCH":
            return self.update_serializer_class
        if self.request.method == "GET":
            if self.kwargs.get('slug') is None:
                if self.request.query_params.get('search') is None:
                    return self.list_serializer_class
                else:
                    return self.search_serializer_class
            else:
                return self.detail_serializer_class
        
    def post(self, request, *args, **kwargs):

        try:

            serializer = self.get_serializer(data=request.data, context={"user": request.user}, many=self.many)

            if serializer.is_valid():
                self.perform_create(serializer)
                if self.unique_control_no:
                    unqiue_no = getattr(serializer.instance, self.unique_control_no, None)
                    create_activity_log(
                        request=request,
                        activity_type=self.created_activity_type_message,
                        content_object=serializer.instance,
                        unique_no=unqiue_no,
                        changes=f"{self.created_activity_changes_message} #{unqiue_no}"
                    )
                return response_message_utils(
                    message=self.success_create_message,
                    status_code=status.HTTP_201_CREATED
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
        
    def get(self, request, *args, **kwargs):
        try:
            
            if kwargs.get('slug') is None:

                queryset = self.get_queryset()

                if request.query_params.get('search') and self.item_to_search:

                    if not self.get_queryset().exists():
                        return response_message_utils(
                            message=self.not_found_search,
                            status_code=status.HTTP_404_NOT_FOUND
                        )
                    
                    paginator = self.pagination_class()

                    paginated_data = paginator.paginate_queryset(queryset, request)
                
                    serializer = self.search_serializer_class(paginated_data, many=True)

                    paginated_response = paginator.get_paginated_response(serializer.data)

                    return response_message_utils(
                        message=self.success_detail_message,
                        data=paginated_response.data,
                        status_code=status.HTTP_200_OK
                    )
                else:
                    # Fall back to list if query param search is None
                    serializer = self.list(queryset)
                    return response_message_utils(
                        message=self.success_list_message,
                        data=serializer.data,
                        status_code=status.HTTP_200_OK
                    )
                
            else:

                if not self.get_queryset().first():
                    return response_message_utils(
                        message=self.not_found_message,
                        status_code=status.HTTP_404_NOT_FOUND
                    )
                
                serializer = self.retrieve(self.get_queryset().first())

                return response_message_utils(
                    message=self.success_detail_message,
                    data=serializer.data,
                    status_code=status.HTTP_200_OK
                )

        except Exception as e:
            return response_message_utils(
                message=f"Something went wrong while processing your request {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    def put(self, request, *args, **kwargs):

        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance=instance, data=request.data)

            if serializer.is_valid():
                serializer.save()
                if self.unique_control_no:
                    unqiue_no = getattr(serializer.instance, self.unique_control_no, None)
                    create_activity_log(
                        request=request,
                        activity_type=self.update_activity_type_message,
                        content_object=serializer.instance,
                        unique_no=unqiue_no,
                        changes=f"{self.update_activity_changes_message} #{unqiue_no}"
                    )
                return response_message_utils(
                    message=self.success_update_message,
                    status_code=status.HTTP_200_OK
                )
            
            return response_message_utils(
                message=extract_first_error_message(serializer.errors),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        except Http404:
            return response_message_utils(
                message=self.not_found_message,
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return response_message_utils(
                message=f"Something went wrong while processing your request {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    def patch(self, request, *args, **kwargs):

        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance=instance, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                if self.unique_control_no:
                    unique_no = getattr(serializer.instance, self.unique_control_no, None)
                    create_activity_log(
                        request=request,
                        activity_type=self.update_activity_type_message,
                        content_object=serializer.instance,
                        unique_no=unique_no,
                        changes=f"{self.update_activity_changes_message} #{unique_no}"
                    )
                return response_message_utils(
                    message=self.success_update_message,
                    status_code=status.HTTP_200_OK
                )
            
            return response_message_utils(
                message=extract_first_error_message(serializer.errors),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        except Http404:
            return response_message_utils(
                message=self.not_found_message,
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return response_message_utils(
                message=f"Something went wrong while processing your request {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    def delete(self, request, *args, **kwargs):
        
        try:

            ids_or_no = request.data.get('ids_or_no')
            # Bulk delete
            if ids_or_no is not None:

                if not isinstance(ids_or_no, list) or len(ids_or_no) < 1:
                    return response_message_utils(
                        errors="ids_or_no` must be a non-empty list.",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                
                valid_uuids = []
                valid_slugs = []

                for val in ids_or_no:
                    try:
                        valid_uuids.append(uuid.UUID(str(val)))
                    except (ValueError, TypeError, AttributeError):
                        valid_slugs.append(val)
                
                purchase_to_delete = self.get_queryset().filter(
                    Q(**{f"{self.lookup_id_field}__in": valid_uuids}) |
                    Q(**{f"{self.lookup_no_field}__in": valid_slugs})
                )

                if purchase_to_delete.count() != len(ids_or_no):
                    return response_message_utils(
                        message=self.not_found_message,
                        status_code=status.HTTP_404_NOT_FOUND
                    )
                
                if self.unique_control_no:
                    u_no = [getattr(obj, self.unique_control_no) for obj in purchase_to_delete if hasattr(obj, self.unique_control_no)]


                    create_activity_log(
                        request=request,
                        activity_type=self.delete_activity_type_message,
                        content_object=purchase_to_delete.first(),
                        unique_no=", ".join(u_no),
                        changes=f"{self.delete_activity_changes_message} #{", ".join(u_no)}"
                    )

                purchase_to_delete.delete()

                return response_message_utils(
                    message=self.success_bulk_delete_message,
                    status_code=status.HTTP_200_OK
                )
            
            purchase_id = kwargs.get(self.lookup_url_kwarg)

            # Single delete
            if purchase_id is not None:

                purchase_to_delete = self.get_queryset()

                if not purchase_to_delete.exists():
                    return response_message_utils(
                        message=self.not_found_message,
                        status_code=status.HTTP_404_NOT_FOUND
                    )
                
                if self.unique_control_no:
                    unique_no = getattr(purchase_to_delete.first(), self.unique_control_no)
                    create_activity_log(
                        request=request,
                        activity_type=self.delete_activity_type_message,
                        content_object=purchase_to_delete.first(),
                        unique_no=unique_no,
                        changes=f"{self.delete_activity_changes_message} #{unique_no}"
                    )
                
      

                self.perform_destroy(purchase_to_delete.first())

                

                return response_message_utils(
                    message=self.success_single_delete_message,
                    status_code=status.HTTP_200_OK
                )

        except Exception as e:
            return response_message_utils(
                message=f"Something went wrong while processing your request {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )