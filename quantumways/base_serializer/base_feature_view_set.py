from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from quantumways.utils import response_message_utils
from rest_framework import status
from quantumways.base_serializer.serializer_action_mixins import SerializerActionByMixin
from quantumways.base_serializer.activity_log_mixins import ActivityLogMixin
from quantumways.base_serializer.bulk_delete_mixins import BulkDeleteMixin
from quantumways.base_serializer.custom_messages_response import CustomMessagesResponse
from quantumways.pagination.main_pagination import CustomPageNumberPagination
from django.db.models import Q

class BaseFeatureViewSet(
    SerializerActionByMixin,
    CustomMessagesResponse,
    ActivityLogMixin,
    BulkDeleteMixin,
    viewsets.ModelViewSet
):
    
    """
        Base class feature with:
        - CRUD
        - Bulk Delete
        - Search
        - Logging
        - Filter
    """
    model = None

    many = False

    permission_classes = [IsAuthenticated]

    pagination_class = CustomPageNumberPagination

    lookup_field = 'id' # Model field used for object lookup in detail routes (e.g., /folders/<id>/)

    lookup_url_kwarg = 'id' # The URL keyword argument that will be used to extract the lookup value from the URL

    # Enable filtering with django filter
    filter_backends = [DjangoFilterBackend]
    filterset_class = None # Override in subclass

    # Field to use for searching data
    item_to_search = None

    # Related optimization
    prefetch_related_model = None # Use for reverse/many-to-many relations
    select_related_model = None # Use for FK/one-to-one relations

    # Action-specific serializers
    serializer_action_classes = {
        "create": None,
        "list": None,
        "retrieve": None,
        "update": None,
        "partial_update": None
    }

    def base_get_queryset(self):
        """
            Base queryset hook. Subclasses can override this
            if needed to prefilter the queryset.
        """
        return self.model.objects.all()

    def get_queryset(self):

        qs = self.base_get_queryset()

        # Apply select_related (FK/OneToOne) if set
        if self.select_related_model:
            qs = qs.select_related(*self.select_related_model)

        # Apply prefetch_related (M2M/Reverse FK) if set
        if self.prefetch_related_model:
            qs = qs.prefetch_related(*self.prefetch_related_model)

        search = self.request.query_params.get('search')
        
        # Apply search filter if both search and item to search set
        if search:

            query = Q()
            for field in self.item_to_search:
                query |= Q(**{f"{field}__icontains": search})
            return qs.filter(query).order_by('created_at')
            
        
        return qs.order_by('created_at')
    
    
    # def retrieve(self, request, *args, **kwargs):
        
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance)

    #     return response_message_utils(
    #         message=self.success_detail_message,
    #         data=serializer.data,
    #         status_code=status.HTTP_200_OK
    #     )
    
    # def list(self, request, *args, **kwargs):

    #     queryset = self.filter_queryset(self.get_queryset())

    #     # Handle pagination
    #     page = self.paginate_queryset(queryset)
    #     if page is not None:
    #         serializer = self.get_serializer(page, many=True)
    #         paginated_data = self.get_paginated_response(serializer.data).data
    #         return response_message_utils(
    #             message=self.success_list_message,
    #             data=paginated_data,
    #             status_code=status.HTTP_200_OK
    #         )

    #     # If no pagination
    #     serializer = self.get_serializer(queryset, many=True)
    #     return response_message_utils(
    #         message=self.success_list_message,
    #         data=serializer.data,
    #         status_code=status.HTTP_200_OK
    #     )
    
    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data, context={"user": request.user}, many=self.many)
        serializer.is_valid(raise_exception=True)

        instance = self.perform_create(serializer)
        
        if hasattr(self, 'log_activity'):
            self.log_activity(request, instance) # Invoke the activity log

        return response_message_utils(
            message=self.success_create_message,
            status_code=status.HTTP_201_CREATED
        )

    def handle_update(self, request, partial):

        instance = self.model.objects.filter(id=self.kwargs.get(self.lookup_field)).first()
        # instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        if hasattr(self, 'log_activity'):
            self.log_activity(request, instance) # Invoke the activity log

        self.perform_update(serializer)

        return response_message_utils(
            message=self.success_update_message,
            status_code=status.HTTP_200_OK
        )

    def update(self, request, *args, **kwargs):
        return self.handle_update(request, False)
    
    def partial_update(self, request, *args, **kwargs):
        return self.handle_update(request, True)

    