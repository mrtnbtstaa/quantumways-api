from rest_framework import generics, status, mixins
from quantumways.utils import response_message_utils
from rest_framework.permissions import IsAuthenticated
from .models import ActivityLog
from rest_framework.permissions import IsAuthenticated
from quantumways.permissions import AllRoles
from rest_framework import generics, mixins
from django.db.models import Q
from .serializers import (
    ViewActivityLogSerializer
)

class ActivityLogView(
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView
):
    permission_classes = [IsAuthenticated, AllRoles]
    serializer_class = ViewActivityLogSerializer
    queryset = ActivityLog.objects.all()
    lookup_field = 'id'
    lookup_url_kwarg = 'activity_log_id'

    def base_get_queryset(self):
        return ActivityLog.objects
    
    def get_queryset(self):
        
        base_qs = self.base_get_queryset()

        if self.request.method == "GET":

            search = self.request.query_params.get('search')

            if search:
                return base_qs.order_by('created_at').filter(
                    Q(changes__icontains=search) |
                    Q(users__first_name__icontains=search) |
                    Q(users__last_name__icontains=search)
                )

            if self.kwargs.get(self.lookup_url_kwarg) is None:
                return base_qs.all().order_by('created_at')
            return base_qs.filter(id=self.kwargs.get(self.lookup_url_kwarg))

        if self.request.method == "DELETE":
            return base_qs.filter(id=self.kwargs.get(self.lookup_url_kwarg))
        
        return base_qs
            
    def get(self, request, *args, **kwargs):

        try:
            
            search = request.query_params.get('search')

            if search is None:

                serializer = self.list(self.get_queryset())

                return response_message_utils(
                    message="List of activity logs",
                    data=serializer.data,
                    status_code=status.HTTP_200_OK
                )
            
            else:

                if not self.get_queryset().exists():
                    return response_message_utils(
                        message="No activity logs found",
                        status_code=status.HTTP_404_NOT_FOUND
                    )
                
                serializer = self.list(self.get_queryset())

                return response_message_utils(
                    message="Found activity logs",
                    data=serializer.data,
                    status_code=status.HTTP_200_OK
                )
            

    
        except Exception as e:
            return response_message_utils(
                message="Something went wrong while processing your request",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    def delete(self, request, *args, **kwargs):

        try:

            delete_activity_log = self.get_queryset()

            if not delete_activity_log.exists():
                return response_message_utils(
                    message="No id found from activity logs",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            self.perform_destroy(delete_activity_log.first())

            return response_message_utils(
                message="Successfully delete",
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            return response_message_utils(
                message="Something went wrong while processing your request",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    




    