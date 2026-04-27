from django.urls import path
from .views import ActivityLogView

urlpatterns = [
    path('v1/activity-logs/', ActivityLogView.as_view(), name='list_activity_logs'),  
    path('v1/activity-logs/<uuid:activity_log_id>/', ActivityLogView.as_view(), name='list_activity_logs'),  
]