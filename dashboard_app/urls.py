from .views import (
    TotalCountV1View,
    TotalCountV2View,
    PurchaseRequestView,
    ActivityLogView,
    UpcomingBirthdayView,
    UpcomingMaintenanceView,
    RepairTrackerViews,
    TotalRepairViews,
    UpcomingMaintenanceViewV2
)
from django.urls import path


urlpatterns = [

    # Dashboard (Purchase Requests, Purchase Orders, Delivery Records) total counts
    path('v1/dashboard/counts/', TotalCountV1View.as_view(), name='dashboard_counts'),
    path('v2/dashboard/counts/', TotalCountV2View.as_view(), name='dashboard_counts'),
 
    path('v1/dashboard/purchase-requests/', PurchaseRequestView.as_view(), name='list_purchase_request'),
    path('v1/dashboard/purchase-requests/<str:uuid_or_no>/', PurchaseRequestView.as_view(), name='details_purchase_request'),

    path('v1/dashboard/activity-logs/', ActivityLogView.as_view(), name='list_activity_logs'),

    path('v1/dashboard/birthdays/', UpcomingBirthdayView.as_view(), name='upcoming_birthdays'),

    path('v1/dashboard/maintenances/', UpcomingMaintenanceView.as_view(), name='upcoming_maintenances'),
    path('v2/dashboard/maintenances/', UpcomingMaintenanceViewV2.as_view(), name='upcoming_maintenances'),

    path('v1/dashboard/repair-tracker/', RepairTrackerViews.as_view(), name='repair_tracker'),
    path('v1/dashboard/total-repair/', TotalRepairViews.as_view(), name='total_repair')

]