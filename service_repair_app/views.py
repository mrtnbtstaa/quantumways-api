from datetime import date, datetime
from quantumways.base_import_view import BaseImportView
from .models import ServiceRepair
from quantumways.base_serializer.base_feature_view_set import BaseFeatureViewSet
from rest_framework import generics, status
from .filter import ServiceRepairFilter
from quantumways.utils import response_message_utils
from quantumways.export_to_excel import export_to_excel
from quantumways.permissions import AllRoles
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    CreateServiceRepairSerializer,
    ListServiceRepairDetailSerializer,
    ListServiceRepairSerializer,
    UpdateServiceRepairSerializer,
    ExistingServiceEquipmentSerializer,
    ImportxlsxInServiceRepairSerializer
)

class ServiceRepairViews(BaseFeatureViewSet):

    model = ServiceRepair

    serializer_action_classes = {
        "create": CreateServiceRepairSerializer,
        "list": ListServiceRepairSerializer,
        "retrieve": ListServiceRepairDetailSerializer,
        "update": UpdateServiceRepairSerializer,
        "partial_update": UpdateServiceRepairSerializer
    }

    filterset_class = ServiceRepairFilter

    item_to_search = ["sr_no"]

    success_create_message = "Successfully created service repair"
    success_delete_message = "Successfully delete the service repair"
    success_update_message = "Successfully update the service repair"
    success_detail_message = "Successfully found service repair"
    success_list_message = "List of service repair"
    not_found_message = "No service repair id found"
    not_found_search = "No service repair found"


class ExistingServiceEquipmentViews(generics.ListAPIView):

    permission_classes = [IsAuthenticated]

    serializer_class = ExistingServiceEquipmentSerializer

    def get_queryset(self):
        return ServiceRepair.objects.only('tools_equipment').all()

    def get(self, request, *args, **kwargs):

        qs = self.get_queryset()

        serializer = self.get_serializer(qs, many=True)

        return response_message_utils(
            message="List of equipments",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
    


class ServiceRepairExportView(generics.ListAPIView):

    permission_classes = [IsAuthenticated, AllRoles]

    def format_list_field(self, value):
        if isinstance(value, list) and value:
            return ", ".join(str(v).upper() for v in value)
        return "N/A"
    
    def parse_char_list_string(self, value):
        if not value:
            return None

        # Already a normal list
        if isinstance(value, list):
            return ",".join(str(v).upper() for v in value)

        if not isinstance(value, str):
            return str(value).upper()

        text = value.strip()

        # Case: string that looks like "[,',R,E,P,L,A...']"
        if text.startswith("[") and text.endswith("]"):

            # Remove brackets
            inner = text[1:-1]

            # Split by comma
            parts = inner.split(",")

            # Keep only single-character tokens (strip quotes)
            chars = []
            for p in parts:
                c = p.strip().strip("'").strip('"')
                if c:
                    chars.append(c)

            # Join characters into full string
            joined = "".join(chars)

            # Convert \N into comma separator
            joined = joined.replace("\\N", ",")

            return joined.upper()

        # Normal plain string fallback
        return text.upper()
    
    def normalize_service_rendered(wsd, fallback):
        if not wsd:
            return fallback
        val = wsd if isinstance(wsd, str) else getattr(wsd, "works_service_done", None)
        if isinstance(val, list):
            return ",".join(str(v).upper() for v in val if v)
        if isinstance(val, str):
            return val.upper()
        return fallback

    def post(self, request, *args, **kwargs):

        try:
            serial_equipment_nos = self.request.data.get('equipment_nos')

            if not ServiceRepair.objects.filter(serial_equipment_number__in=serial_equipment_nos).exists():
                return response_message_utils(
                    message="No equipment no found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            # Header Row
            header = [
                "EQUIPMENT",
                "EQUIPMENT NO.",
                "DATE",
                "SR NO",
                "REPAIR NO",
                "SITE",
                "COLOR",
                "STATUS",
                "SERVICE TYPE",
                "SERVICE DATE",
                "LAST REPAIRED",
                "LAST REPLACEMENT",
                "LAST MAINTENANCE",
                "PROBLEMS ENCOUNTERED",
                "SERVICE RENDERED",
                "MATERIALS PURCHASED",
                "QUANTITY",
                "REPAIRED BY",
                "DATE STARTED",
                "DATE COMPLETED",
                "REQUESTED BY",
                "NOTED BY",
                "APPROVED BY",
                "REMARKS"
            ]

            services = (
                ServiceRepair.objects
                .order_by('created_at')
                .filter(serial_equipment_number__in=serial_equipment_nos)
            )

            raw_rows = []

            # original_equipment = equipment.order_by('equipment').filter(is_created_equipment=True)

            # snapshots = []
            # Iterate over the original equipments

            for i, service in enumerate(services):

                equipment_log = getattr(service, 'equipment_log', None)

                materials = list(service.materials.all())

                for j, material in enumerate(materials):

                    raw_rows.append([
                        service.tools_equipment.upper() or "N/A",
                        service.serial_equipment_number.upper() or "N/A",
                        service.date or "N/A",
                        service.sr_no.upper() or "N/A",
                        service.repair_no.upper() or "N/A",
                        service.site.upper() or "N/A",
                        service.color.upper() or "N/A",
                        str(equipment_log.status).upper() or "N/A",
                        equipment_log.action_type.upper() or "N/A",
                        equipment_log.action_date or None,
                        equipment_log.last_repaired or None,
                        equipment_log.last_replacement or None,
                        equipment_log.last_maintenance or None,
                        equipment_log.problems_encountered.upper() or "N/A",
                        self.format_list_field(equipment_log.works_service_done),
                        str(material.items).upper() or "N/A",
                        material.quantity or "N/A",
                        service.repaired_by.upper() or "N/A",
                        service.date_started or None,
                        service.date_completed or None,
                        service.requested_by.upper() or "N/A",
                        service.noted_by.upper() or "N/A",
                        service.approved_by.upper() or "N/A",
                        service.remarks.upper() or "N/A"
                    ])


            # Collect only the unique service repair records
            # service_repairs_unique = {}

            # for eq in equipment.filter(is_created_equipment=False):
            #     # Store the key where key is the repair's primary key
            #     for repair in eq.service_repairs.order_by('created_at').all():
            #         service_repairs_unique[repair.pk] = repair

            # # Convert unique repair objects back to a list
            # service_repairs_queryset = list(service_repairs_unique.values())

            # for repair in service_repairs_queryset:
                
            #     equipments = repair.equipments.filter(is_created_equipment=False)
                
            #     for eq in equipments:
                    
            #         if not eq:
            #             continue

            #         raw_rows.append([
            #             # Equipment Details (based on the current 'eq' object)
            #             eq.equipment.upper() if eq.equipment else None,
            #             eq.equipment_no if eq.equipment_no else None,
            #             eq.status.upper() if eq.status else None,
            #             eq.plate_no if eq.plate_no else None,
            #             eq.site.upper() if eq.site else None,
            #             eq.color.upper() if eq.color else None,
            #             eq.chasis_no.upper() if eq.chasis_no else None,
            #             eq.brand_name.upper() if eq.brand_name else None,
            #             eq.model if eq.model else None,
            #             eq.last_inspection if eq.last_inspection else None,
            #             eq.last_registration if eq.last_registration else None,
            #             eq.next_registration if eq.next_registration else None,
            #             eq.last_conduct_of_pm if eq.last_conduct_of_pm else None,
            #             eq.next_pm if eq.next_pm else None,
            #         ])

            final_rows = raw_rows

            # Sort by the equipment field
            final_rows.sort(key=lambda x: x[0], reverse=False)

            formatters = {
                2: lambda d: d.strftime('%d-%b-%Y') if isinstance(d, (date, datetime)) else d,
                9: lambda d: d.strftime('%d-%b-%Y') if isinstance(d, (date, datetime)) else d,
                10: lambda d: d.strftime('%d-%b-%Y') if isinstance(d, (date, datetime)) else d,
                11: lambda d: d.strftime('%d-%b-%Y') if isinstance(d, (date, datetime)) else d,
                12: lambda d: d.strftime('%d-%b-%Y') if isinstance(d, (date, datetime)) else d,
                18: lambda d: d.strftime('%d-%b-%Y') if isinstance(d, (date, datetime)) else d,
                19: lambda d: d.strftime('%d-%b-%Y') if isinstance(d, (date, datetime)) else d,
            }

            return export_to_excel(
                headers=header,
                file_name="service_repairs_",
                queryset=final_rows,
                formatters=formatters,
                title="ServiceRepairs"
            )

        except Exception as e:
            return response_message_utils(
                message=f"Something went wrong while exporting your excel {e} 13123123",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class ServiceREpairImportView(BaseImportView):

    serializer_class = ImportxlsxInServiceRepairSerializer

    queryset = ServiceRepair.objects.all()

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
                message=f"Something went wrong: {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )  
    
    




