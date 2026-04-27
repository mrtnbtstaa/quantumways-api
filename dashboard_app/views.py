from quantumways.utils import response_message_utils
from rest_framework import generics, status
from purchase_request_app.models import PurchaseRequest
from purchase_order_app.models import PurchaseOrder 
from delivery_record_app.models import DeliveryRecord
from activity_log_app.models import ActivityLog
from datetime import timedelta
from django.utils.timezone import now
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from authentication_app.models import User
from quantumways.constants import Role
from django.db.models import Q, F, Count, OuterRef, Subquery
from django.db.models.functions import ExtractMonth, ExtractDay
from datetime import datetime
from master_list_app.models import Equipment, EquipmentStatus
from service_repair_app.models import ServiceRepair
import uuid
from rest_framework.pagination import PageNumberPagination

class DashboardPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'limit'
    max_page_size = 100
    page_query_param = 'page'

from .serializers import (
    ListPurchaseRequestSerializer,
    ViewPurchaseRequestDetailstSerializer,
    ListActivityLogSerializer,
    ListOfUpcomingBirthdaySerializer,
    UpcomingMaintenanceSerializerV2
)

class TotalCountV1View(generics.ListAPIView):

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        
        today = now().date()

        date_param = self.request.query_params.get("date")  # Date query param

        if date_param == "last_day":
            start_date = today - timedelta(days=1)
        elif date_param == "last_15_days":
            start_date = today - timedelta(days=15)
        elif date_param == "last_month":
            start_date = today - timedelta(days=31)
        else:
            start_date = today # Fallback to today 

        pr_count = PurchaseRequest.objects.filter(created_at__date__gte=start_date).count()
        po_count = PurchaseOrder.objects.filter(created_at__date__gte=start_date).count()
        dr_count = DeliveryRecord.objects.filter(created_at__date__gte=start_date).count()

        return {
            "purchase_request_total": pr_count,
            "purchase_order_total": po_count,
            "delivery_record_total": dr_count
        }

    def list(self, request, *args, **kwargs):

        try:
            
            data = self.get_queryset()

            return response_message_utils(
                message="Total counts",
                data=data,
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            return response_message_utils(
                message="Something went wrong while processing the requests",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class TotalCountV2View(generics.ListAPIView):

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        
        today = timezone.localdate()

        first_day = today.replace(day=1)

        if today.month == 12:
            last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last_day = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

        equipment = Equipment.objects.filter(is_created_equipment=True)

        total_ongoing_repair = equipment.filter(status=EquipmentStatus.ONGOING_REPAIR).count()
        total_under_maintenance = equipment.filter(status=EquipmentStatus.UNDER_MAINTENANCE).count()
        active_service_vehicle = equipment.filter(status=EquipmentStatus.ACTIVE)
        total_active_service_vehicle = active_service_vehicle.count()
        total_upcoming_pm_of_the_month = Equipment.objects.filter(next_pm__range=(first_day, last_day)).count()

        total_vehicle = equipment.aggregate(
            total_registered_vehicle=Count('id', filter=Q(next_registration__gt=today)), # Still valid
            total_vehicle_for_registration=Count('id', filter=Q(next_registration__lte=today)) # Expired
        )

        total_registered_vehicle = total_vehicle.get('total_registered_vehicle')
        total_vehicle_for_registration = total_vehicle.get('total_vehicle_for_registration')

        return {
            "total_ongoing_repair": total_ongoing_repair,
            "total_under_maintenance": total_under_maintenance,
            "total_active_service_vehicle": total_active_service_vehicle,
            "total_upcoming_pm_of_the_month": total_upcoming_pm_of_the_month,
            "total_registered_vehicle": total_registered_vehicle,
            "total_vehicle_for_registration": total_vehicle_for_registration
        }

    def list(self, request, *args, **kwargs):

        try:
            
            data = self.get_queryset()

            return response_message_utils(
                message="Total counts",
                data=data,
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            return response_message_utils(
                message="Something went wrong while processing the requests",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class RepairTrackerViews(generics.ListAPIView):

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        
        current_year = timezone.localdate().year

        return (
            ServiceRepair.objects
            .filter(created_at__year=current_year, date_completed__isnull=False)
            .values('tools_equipment')
            .annotate(total_repairs=Count('id')) 
        )


    def get(self, request, *args, **kwargs):
        
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)

        if page is not None:

            data = [
                {
                    **obj
                }
                for obj in page
            ]

            return self.get_paginated_response(data)
    

class TotalRepairViews(generics.ListAPIView):

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        
        current_year = timezone.localdate().year
        today = timezone.localdate()
        
        first_service = (
            ServiceRepair.objects
            .filter(tools_equipment=OuterRef('tools_equipment'))
        )

        first_records = ServiceRepair.objects.filter(
            id__in=Subquery(
                ServiceRepair.objects
                .values('tools_equipment') # Group by tools equipment
                .annotate(first_id=Subquery(first_service.values('id')[:1]))
                .values('first_id')
            )
        )

        color_map = {sr.tools_equipment.lower(): sr.color for sr in first_records}

        total_repairs = ServiceRepair.objects.filter(
            date_completed__isnull=False,
            created_at__year=current_year
        ).count()

        repairs = (
            ServiceRepair.objects
            .filter(date_completed__isnull=False, created_at__year=current_year)
            .values('tools_equipment')
            .annotate(total_repairs=Count('id'))
        )

        repairs_with_colors = [
            {
                **repair,
                "color": color_map.get(str(repair["tools_equipment"]).lower(), "#CCCCCC")  # default gray
            }
            for repair in repairs
        ]

        return {
            "total_repairs": total_repairs,
            "equipment": repairs_with_colors
        }


    def get(self, request, *args, **kwargs):
        
        return response_message_utils(
            message="List of total repairs",
            data=self.get_queryset()
        )


class PurchaseRequestView(
    generics.GenericAPIView
):

    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'uuid_or_no'
    lookup_field = 'id'

    def get_serializer_class(self):

        if self.request.method == "GET":
            if self.kwargs.get(self.lookup_url_kwarg) is None:
                return ListPurchaseRequestSerializer
            return ViewPurchaseRequestDetailstSerializer

    def base_queryset(self):
        return PurchaseRequest.objects

    def get_lookup(self):

        base_qs = self.base_queryset()

        lookup = self.kwargs.get(self.lookup_url_kwarg) 
        try:
            uuid_val = uuid.UUID(lookup) 
            return base_qs.filter(id=uuid_val)
        except ValueError:
            return base_qs.filter(pr_no=lookup)

    def get_queryset(self):

        base_qs = self.base_queryset()

        if self.request.method == "GET":
            if self.kwargs.get(self.lookup_url_kwarg) is None:
                now = timezone.now()
                past_24_hrs = now - timedelta(hours=24)
                return base_qs.filter(created_at__gte=past_24_hrs)
            return self.get_lookup()
        
        return self.get_lookup()

    def get(self, request, *args, **kwargs):

        try:
            
            if kwargs.get(self.lookup_url_kwarg):

                queryset = self.get_queryset().first()

                if not queryset:
                    return response_message_utils(
                        message="No purchase requests found",
                        status_code=status.HTTP_404_NOT_FOUND
                    )

                serializer = self.get_serializer(queryset, many=False)

                return response_message_utils(
                    message="Purchase Requests",
                    data=serializer.data,
                    status_code=status.HTTP_200_OK
                )
        
            queryset = self.get_queryset()

            serializer = self.get_serializer(queryset, many=True)

            return response_message_utils(
                message="List of purchase requests",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            return response_message_utils(
                message="Something went wrong while processing your requests",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    def delete(self, request, *args, **kwargs):

        try:

            queryset = self.get_queryset().first()

            if not queryset:
                return response_message_utils(
                    message="No purchase requests found",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            queryset.delete()

            return response_message_utils(
                message="Successfully delete the purchase requests",
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            return response_message_utils(
                message="Something went wrong while processing your requests",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class ActivityLogView(
    generics.GenericAPIView
):

    permission_classes = [IsAuthenticated]
    serializer_class = ListActivityLogSerializer


    def get_queryset(self):

        now = timezone.now()
        past_24_hrs = now - timedelta(hours=24)
        return ActivityLog.objects.select_related('users').filter(created_at__gte=past_24_hrs)

    def get(self, request, *args, **kwargs):

        try:
            
            queryset = self.get_queryset()

            serializer = self.get_serializer(queryset, many=True)

            return response_message_utils(
                message="List of Activity logs",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
                
        except Exception as e:
            return response_message_utils(
                message="Something went wrong while processing your requests",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class UpcomingBirthdayView(
    generics.GenericAPIView
):
    serializer_class = ListOfUpcomingBirthdaySerializer
    permission_classes = [IsAuthenticated]

    def base_queryset(self):
        return User.objects.select_related('user_information', 'user_profile').filter(user_role__role__in=Role.ROLES)

    def get_queryset(self):

        today = datetime.today().date()

        next_month = today + timedelta(days=31)

        # Extract month and day for comparison
        today_md = today.month * 100 + today.day
        next_month_md = next_month.month * 100 + next_month.day

        qs = self.base_queryset().annotate(
            birth_month=ExtractMonth(F('user_information__birth_date')),
            birth_day=ExtractDay(F('user_information__birth_date'))
        ).annotate(
            birthday_md=F('birth_month') * 100 + F('birth_day')
        )

        if next_month_md >= today_md:
            return qs.filter(birthday_md__gte=today_md, birthday_md__lte=next_month_md)
        else:
            # Wraps around case like December to January
            return qs.filter(Q(birthday_md__gte=today_md) | Q(birthday_md__lte=next_month_md))

    def get(self, request, *args, **kwargs):

        try:
            
            queryset = self.get_queryset()

            serializer = self.get_serializer(queryset, many=True)

            return response_message_utils(
                message="List of upcoming birthday",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
                
        except Exception as e:
            return response_message_utils(
                message=f"Something went wrong while processing your requests {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        


class UpcomingMaintenanceView(
    generics.GenericAPIView
):

    permission_classes = [IsAuthenticated]

    def base_queryset(self):
        return Equipment.objects.all()

    def get_queryset(self):
        base_qs = self.base_queryset()
        today = datetime.today().date()
        next_month = today + timedelta(days=31)

        data = []

        for equipment in base_qs:

            next_pm = equipment.next_pm

            if today <= next_pm <= next_month:
                data.append({
                    "equipment_no": equipment.equipment_no,
                    "equipment_name": equipment.equipment_type,
                    "model_name": equipment.model_name,
                    "last_conduct_of_pm": datetime.strptime(equipment.last_conduct_of_pm, '%m-%d-%Y').date(),
                    "next_pm": equipment.next_pm.strftime('%d-%b-%Y'),
                    "remarks": equipment.remarks
                })

        return data

    def get(self, request, *args, **kwargs):

        try:
            
            queryset = self.get_queryset()


            return response_message_utils(
                message="List of upcoming maintenance",
                data=queryset,
                status_code=status.HTTP_200_OK
            )
                
        except Exception as e:
            return response_message_utils(
                message="Something went wrong while processing your requests",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpcomingMaintenanceViewV2(generics.ListAPIView):

    permission_classes = [IsAuthenticated]

    serializer_class = UpcomingMaintenanceSerializerV2
    pagination_class = DashboardPagination

    def get_queryset(self):

        today = timezone.localdate()
        return Equipment.objects.filter(next_pm__gt=today).order_by('created_at')
    

    def get(self, request, *args, **kwargs):
        
        serializer = self.get_serializer(self.get_queryset())

        paginated = self.list(serializer)

        return response_message_utils(
            message="List of upcoming maintenance",
            data=paginated.data,
            status_code=status.HTTP_200_OK
        )
    

        

