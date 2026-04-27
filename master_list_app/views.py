from rest_framework import generics, status, mixins
from rest_framework.response import Response
from quantumways.utils import response_message_utils
from quantumways.permissions import  AllRoles
from rest_framework.permissions import IsAuthenticated
from .models import Supplier, Product, Equipment, EquipmentSnapshot, EquipmentStatus
from datetime import date, datetime
from quantumways.export_to_excel import export_to_excel
from quantumways.base_feature_view import BaseFeatureView
from quantumways.base_import_view import BaseImportView
from quantumways.base_serializer.base_feature_view_set import BaseFeatureViewSet
from collections import Counter
from django.db.models import OuterRef, Subquery
from rest_framework.permissions import IsAuthenticated
from quantumways.utils import extract_first_error_message
from collections import OrderedDict, defaultdict
import ast
from itertools import zip_longest
from rest_framework.decorators import action
import json
import re

from .serializers import (

    AddMasterListSupplierSerializer,
    ViewMasterListSupplierSerializer,
    UpdateMasterListSupplierSerializer,
    SearchMasterListSupplierSerializer,

    AddMasterListProductSerializer,
    ViewMasterListProductSerializer,
    ViewMasterListDetailsProductSerializer,
    UpdateMasterListProductSerializer,
    SearchMasterListProductSerializer,

    AddMasterListEquipmentSerializer,
    ViewMasterListEquipmentSerializer,
    ViewMasterListDetailsEquipmentSerializer,
    UpdateMasterListEquipmentSerializer,
    SearchMasterListEquipmentSerializer,

    ImportxlsxInMasterListSuppliersSerializer,
    ImportxlsxInMasterListProductsSerializer,
    ImportxlsxInMasterListEquipmentsSerializer,

    ExistingSupplierMasterListSerializer,
    ExistingProductMasterListSerializer,

    ImportxlsxInMasterListEquipmentsV2Serializer,
    ImportxlsxInMasterListEquipmentsV3Serializer,

    CreateEquipmentV2Serializer,
    ListEquipmentV2Serializer,
    ListEquipmentDetailsV2Serializer,
    ListGroupEquipmentDetailsV2Serializer,
    UpdateMasterlistEquipmentV2Serializer,
    DropdownItemEquipmentSerializer,

    EquipmentLookupSerializer,
    DropdownSerialEquipmentNumberSerializer

)

# ------- EQUIPMENT VIEW -------------------

class MasterListSupplierView(BaseFeatureView):

    model = Supplier

    lookup_no_field = 'id'

    create_serializer_class = AddMasterListSupplierSerializer
    list_serializer_class = ViewMasterListSupplierSerializer
    detail_serializer_class = ViewMasterListSupplierSerializer
    update_serializer_class = UpdateMasterListSupplierSerializer
    search_serializer_class = SearchMasterListSupplierSerializer

    success_create_message = "Successfully added suppliers"
    success_list_message = "List of suppliers"
    success_detail_message = "Successfully found supplier"
    success_update_message = "Successfully update the suppliers"
    success_bulk_delete_message = "Successfully delete the suppliers"
    success_single_delete_message = "Successfully delete the supplier"
    not_found_message = "No id found from the suppliers"
    not_found_search = "No item found"

    many = False

    item_to_search = "item__icontains"


class MasterListSuppliersImportView(BaseImportView):
    
    serializer_class = ImportxlsxInMasterListSuppliersSerializer

    queryset = Supplier.objects.all()
            

class MasterListSuppliersExportView(generics.CreateAPIView):

    permission_classes = [IsAuthenticated, AllRoles]

    def post(self, request, *args, **kwargs):

        try:

            suppliers_ids = self.request.data.get('ids')

            if not Supplier.objects.filter(id__in=suppliers_ids).exists():
                return response_message_utils(
                    message="No id found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            # Define the header row
            header = [
                "NO.",
                "ITEM",
            ]

            rows = []

            # Get data
            queryset = Supplier.objects.filter(id__in=suppliers_ids).order_by('created_at')
            
            for obj in queryset:
                row = [
                    obj.no,
                    obj.item
                ]
                rows.append(row)            

            formatters = {
                1: lambda d: str(d).strip()
            }

            return export_to_excel(
                headers=header,
                file_name="master_list_suppliers_",
                queryset=rows,
                title="Suppliers",
                formatters=formatters
            )

        except Exception as e:
            return response_message_utils(
                message=f"Something went wrong while exporting your excel {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

# ------- EQUIPMENT VIEW -------------------

# ------- PRODUCT VIEW -------------------

class MasterListProductView(BaseFeatureView):

    model = Product

    lookup_no_field = 'id'

    create_serializer_class = AddMasterListProductSerializer
    list_serializer_class = ViewMasterListProductSerializer
    detail_serializer_class = ViewMasterListDetailsProductSerializer
    update_serializer_class = UpdateMasterListProductSerializer
    search_serializer_class = SearchMasterListProductSerializer

    success_create_message = "Successfully added products"
    success_list_message = "List of products"
    success_detail_message = "Successfully found a product"
    success_update_message = "Successfully update the products"
    success_bulk_delete_message = "Successfully delete the products"
    success_single_delete_message = "Successfully delete the product"
    not_found_message = "No id found from the products"
    not_found_search = "No item found"

    many = False

    item_to_search = 'item__icontains'


class MasterListProductsImportView(BaseImportView):

    serializer_class = ImportxlsxInMasterListProductsSerializer

    queryset = Supplier.objects.all()
        
  
class MasterListProductsExportView(generics.CreateAPIView):

    permission_classes = [IsAuthenticated, AllRoles]

    def post(self, request, *args, **kwargs):

        try:

            products_ids = self.request.data.get('ids')

            if not Product.objects.filter(id__in=products_ids).exists():
                return response_message_utils(
                    message="No id found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            # Define the header row
            header = [
                "NO.",
                "ITEM",
                "UNIT",
                "PRICE",
            ]
            rows = []
            # Get data
            queryset = (
                Product.objects
                .filter(id__in=products_ids).order_by('created_at')
            )

            for obj in queryset:
                row = [
                    obj.no,
                    obj.item,
                    obj.unit,
                    obj.price
                ]
                rows.append(row)


            formatters = {
                1: lambda d: str(d).strip()
            }

            return export_to_excel(
                headers=header,
                file_name="master_list_products_",
                queryset=rows,
                title="Products",
                formatters=formatters
            )

        except Exception as e:
            return response_message_utils(
                message=f"Something went wrong while exporting your excel {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
# --------- PRODUCT VIEW --------------------------------------


# ------- EQUIPMENT VIEW -------------------

class MasterListEquipmentView(BaseFeatureView):

    model = Equipment

    lookup_no_field = 'id'

    create_serializer_class = AddMasterListEquipmentSerializer
    list_serializer_class = ViewMasterListEquipmentSerializer
    detail_serializer_class = ViewMasterListDetailsEquipmentSerializer
    update_serializer_class = UpdateMasterListEquipmentSerializer
    search_serializer_class = SearchMasterListEquipmentSerializer

    success_create_message = "Successfully added equipments"
    success_list_message = "List of equipments"
    success_detail_message = "Successfully found equipment"
    success_update_message = "Successfully update the equipments"
    success_bulk_delete_message = "Successfully delete the equipments"
    success_single_delete_message = "Successfully delete the equipment"
    not_found_message = "No id found from the equipments"
    not_found_search = "No equipment found"

    many = False

    item_to_search = "equipment_name__icontains"


    
class MasterListEquipmentImportView(BaseImportView):

    serializer_class = ImportxlsxInMasterListEquipmentsSerializer

    queryset = Equipment.objects.all()
              

class MasterListEquipmentExportView(generics.ListAPIView):

    permission_classes = [IsAuthenticated, AllRoles]

    def post(self, request, *args, **kwargs):

        try:

            equipment_ids = self.request.data.get('ids')

            if not Equipment.objects.filter(id__in=equipment_ids).exists():
                return response_message_utils(
                    message="No id found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            # Define the header row
            header = [
                "#",
                "Equipment No.",
                "Model Name",
                "Equipment Name",
                "Last Conduct of PM",
                "Next PM",
                "Remarks"
            ]

            # Get data
            queryset = (
                Equipment.objects
                .filter(id__in=equipment_ids).values_list(
                    "no",
                    "equipment_no",
                    "model_name",
                    "equipment_name",
                    "last_conduct_of_pm",
                    "next_pm",
                    "remarks"
                ).order_by('created_at')
            )

            formatters = {
                4: lambda d: d.strftime('%d-%b-%Y') if isinstance(d, (date, datetime)) else d,
                5: lambda d : d.strftime('%B-%Y') if isinstance(d, (date, datetime)) else d
            }

            return export_to_excel(
                headers=header,
                file_name="master_list_equipments_",
                queryset=queryset,
                formatters=formatters,
                title="Equipments"
            )

        except Exception as e:
            return response_message_utils(
                message=f"Something went wrong while exporting your excel {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        
# --------- EQUIPMENT VIEW --------------------------------------
class ViewExistingSupplierMasterList(generics.ListAPIView):

    pagination_class = None
    serializer_class = ExistingSupplierMasterListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Supplier.objects.all()
    
    def list(self, request, *args, **kwargs):

        try:

            serializer = self.get_serializer(self.get_queryset(), many=True)

            return response_message_utils(
                message="List of suppliers",
                data=serializer.data
            )

        except Exception as e:
            return response_message_utils(
                message=f"Something went wrong while exporting your excel {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class ViewExistingProductMasterList(generics.ListAPIView):

    pagination_class = None
    serializer_class = ExistingProductMasterListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Product.objects.all()
    
    def list(self, request, *args, **kwargs):

        try:

            serializer = self.get_serializer(self.get_queryset(), many=True)

            return response_message_utils(
                message="List of products",
                data=serializer.data
            )

        except Exception as e:
            return response_message_utils(
                message=f"Something went wrong while exporting your excel {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

# --------------------------- MASTERLIST EQUIPMENT V2 --------------------------------------------

class MasterListEquipmentV2ImportView(BaseImportView):

    serializer_class = ImportxlsxInMasterListEquipmentsV2Serializer

    queryset = Equipment.objects.all()

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

class MasterListEquipmentV2ExportView(generics.ListAPIView):

    permission_classes = [IsAuthenticated, AllRoles]

    def once_displayed(self, queryset, fields):

        field_counters = {f: Counter() for f in fields}

        for eq in queryset:
            for f in fields:
                value = getattr(eq, f, None)

                if value:
                    field_counters[f][value] += 1

        # Track which values have been displayed
        displayed_fields = {f: set() for f in fields}


        def display(field_name, value):
            if not value:
                return None
            counts = field_counters[field_name]
            displayed = displayed_fields[field_name]

            if counts[value] == 1:  # only appears once in all queryset
                return value
            if value not in displayed:
                displayed.add(value)
                return value
            return None  # duplicate after first display

        return display
    
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
            equipment_nos = self.request.data.get('equipment_nos')

            if not Equipment.objects.filter(equipment_no__in=equipment_nos).exists():
                return response_message_utils(
                    message="No equipment no found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            # Header Row
            header = [
                "EQUIPMENT",
                "EQUIPMENT NO.",
                "STATUS",
                "PLATE NO",
                "SITE",
                "COLOR",
                "CHASIS NO",
                "BRAND NAME",
                "MODEL",
                "LAST INSPECTION",
                "LAST REGISTRATION",
                "NEXT REGISTRATION",
                "LAST CONDUCT OF PM",
                "NEXT PM",
                "SERVICE RENDERED",
                "DATE",
                "SR NO",
                "REPAIR NO",
                "PROBLEMS ENCOUNTERED",
                "MATERIALS PURCHASED",
                "QUANTITY",
                "MECHANIC",
                "REMARKS"
            ]

            equipment = (
                Equipment.objects
                .order_by('created_at')
                .filter(equipment_no__in=equipment_nos, status=EquipmentStatus.ACTIVE)
            )

            # Returns the paired item and quantity
            def paired_item_qty(eq, material):
                return material.items if material else None, material.quantity if material else None
            
            raw_rows = []

            original_equipment = equipment.order_by('equipment').filter(is_created_equipment=True)

            snapshots = []
            # Iterate over the original equipments
            for orig_eq in original_equipment:

                equipment_log = None
                sr = None

                # service_rendered_value = ",".join(s for s in orig_eq.service_rendered.upper()) if isinstance(orig_eq.service_rendered, list) else None
                service_rendered_value = self.format_list_field(orig_eq.service_rendered) if orig_eq.service_rendered else "N/A"
                
                if orig_eq.service_repairs.first():
                    sr = getattr(orig_eq, 'service_repairs', None).first()
                    equipment_log = getattr(sr, 'equipment_log', None)

                    works_service_done_value = self.parse_char_list_string(equipment_log.works_service_done)

                    # print(works_service_done_value)
                    # works_service_done_value = ",".join(s for s in equipment_log.works_service_done) if isinstance(equipment_log.works_service_done, str) else None
                    # Append the original equipment
                    raw_rows.append([
                        orig_eq.equipment.upper() if orig_eq.equipment else None,
                        orig_eq.equipment_no if orig_eq.equipment_no else None,
                        orig_eq.status.upper() if orig_eq.status else None,
                        orig_eq.plate_no if orig_eq.plate_no else None,
                        orig_eq.site.upper() if orig_eq.site else None,
                        orig_eq.color.upper() if orig_eq.color else None,
                        orig_eq.chasis_no.upper() if orig_eq.chasis_no else None,
                        orig_eq.brand_name.upper() if orig_eq.brand_name else None,
                        orig_eq.model if orig_eq.model else None,
                        orig_eq.last_inspection if orig_eq.last_inspection else None,
                        orig_eq.last_registration if orig_eq.last_registration else None,
                        orig_eq.next_registration if orig_eq.next_registration else None,
                        orig_eq.last_conduct_of_pm if orig_eq.last_conduct_of_pm else None,
                        orig_eq.next_pm if orig_eq.next_pm else None,
                        service_rendered_value if service_rendered_value else works_service_done_value if equipment_log else None,
                        sr.date if sr else None,
                        sr.sr_no if sr else None,
                        sr.repair_no if sr else None,
                        self.format_list_field(orig_eq.problems_encountered) if orig_eq.service_rendered else "N/A",
                        orig_eq.materials_purchased.upper() if orig_eq.materials_purchased else "N/A",
                        orig_eq.quantity,
                        orig_eq.mechanic.upper() if orig_eq.mechanic else "N/A",
                        orig_eq.remarks.upper() if orig_eq.remarks else "N/A",
                    ])
                else:
                    raw_rows.append([
                        orig_eq.equipment.upper() if orig_eq.equipment else "N/A",
                        orig_eq.equipment_no if orig_eq.equipment_no else "N/A",
                        orig_eq.status.upper() if orig_eq.status else "N/A",
                        orig_eq.plate_no if orig_eq.plate_no else "N/A",
                        orig_eq.site.upper() if orig_eq.site else "N/A",
                        orig_eq.color.upper() if orig_eq.color else "N/A",
                        orig_eq.chasis_no.upper() if orig_eq.chasis_no else "N/A",
                        orig_eq.brand_name.upper() if orig_eq.brand_name else "N/A",
                        orig_eq.model if orig_eq.model else "N/A",
                        orig_eq.last_inspection if orig_eq.last_inspection else "N/A",
                        orig_eq.last_registration if orig_eq.last_registration else "N/A",
                        orig_eq.next_registration if orig_eq.next_registration else "N/A",
                        orig_eq.last_conduct_of_pm if orig_eq.last_conduct_of_pm else "N/A",
                        orig_eq.next_pm if orig_eq.next_pm else "N/A",
                        service_rendered_value,
                        "N/A",
                        "N/A",
                        "N/A",
                        self.format_list_field(orig_eq.problems_encountered) if orig_eq.service_rendered else "N/A",
                        orig_eq.materials_purchased.upper() if orig_eq.materials_purchased else "N/A",
                        orig_eq.quantity,
                        orig_eq.mechanic.upper() if orig_eq.mechanic else "N/A",
                        orig_eq.remarks.upper() if orig_eq.remarks else "N/A",
                    ])

                # Resolve service_rendered list
                if orig_eq.service_rendered:
                    service_rendered_snapshot = orig_eq.service_rendered
                elif equipment_log and equipment_log.works_service_done:
                    service_rendered_snapshot = equipment_log.works_service_done
                else:
                    service_rendered_snapshot = []

                # Resolve problems_encountered list
                if orig_eq.problems_encountered:
                    problems_snapshot = orig_eq.problems_encountered
                elif equipment_log and equipment_log.problems_encountered:
                    problems_snapshot = equipment_log.problems_encountered
                else:
                    problems_snapshot = []

                # Save the original equipment to the EquipmentSnapshot
                if not EquipmentSnapshot.objects.filter(equipment=str(orig_eq.equipment).upper()).exists():
                    snapshots.append(EquipmentSnapshot(
                        equipment=orig_eq.equipment.upper() if orig_eq.equipment else None,
                        service_rendered=service_rendered_snapshot,
                        problems_encountered=problems_snapshot,
                        materials_purchased=orig_eq.materials_purchased.upper() if orig_eq.materials_purchased else sr.materials.first().items.upper() if sr and sr.materials.first() else None,
                        quantity=orig_eq.quantity,
                        mechanic=orig_eq.mechanic.upper() if orig_eq.mechanic else sr.repaired_by.upper() if sr and sr.repaired_by else None,
                        remarks=orig_eq.remarks.upper() if orig_eq.remarks else sr.remarks.upper() if sr and sr.remarks else None,
                        sr_no=sr.sr_no if sr else None,
                        equipment_no=orig_eq.equipment_no,
                        is_created_equipment=True
                    ))

            EquipmentSnapshot.objects.bulk_create(snapshots)

            # Collect only the unique service repair records
            service_repairs_unique = {}

            for eq in equipment.filter(is_created_equipment=False):
                # Store the key where key is the repair's primary key
                for repair in eq.service_repairs.order_by('created_at').all():
                    service_repairs_unique[repair.pk] = repair

            # Convert unique repair objects back to a list
            service_repairs_queryset = list(service_repairs_unique.values())

            for repair in service_repairs_queryset:
                
                equipments = repair.equipments.filter(is_created_equipment=False)
                materials = repair.materials.all()

                equipment_log = getattr(repair, 'equipment_log', None)

                for material, eq in zip(materials, equipments):
                    
                    if not eq:
                        continue

                    # Get Repair-specific details (same for all rows of this repair)
                    d = repair.date
                    s = repair.sr_no
                    r = repair.repair_no
                    
                    # Determine Works Service Done (WSD) value
                    wsd = self.parse_char_list_string(repair.equipment_log.works_service_done if repair.equipment_log and repair.equipment_log.works_service_done else None)
                    
                    # srv = parse_char_list_string(eq.service_rendered)
                    # wsd = None
                    # wsd = repair.equipment_log.works_service_done.upper() \
                    #     if repair.equipment_log and repair.equipment_log.works_service_done else None

                    srv = self.format_list_field(eq.service_rendered) if eq.service_rendered else "N/A"
                    # if isinstance(eq.service_rendered, list) and eq.service_rendered:
                    #     try:
                    #         srv = ",".join([str(item) for item in eq.service_rendered])
                    #         # srv = ",".join(eq.service_rendered.upper())
                    #     except Exception:
                    #         pass
                    #         srv = ",".join([str(item) for item in eq.service_rendered])

                    mechanic_val = eq.mechanic.upper() if eq.mechanic else "N/A"
                    remarks_val = eq.remarks.upper() if eq.remarks else "N/A"

                    print(f"WSD: {wsd}")
                    print(f"SRV: {srv}")

                    _, qty_val = paired_item_qty(eq, material)
                    
                    # wsd = parse_db_list(repair.equipment_log.works_service_done)
                    # srv = parse_db_list(eq.service_rendered)

                    raw_rows.append([
                        # Equipment Details (based on the current 'eq' object)
                        eq.equipment.upper() if eq.equipment else None,
                        eq.equipment_no if eq.equipment_no else None,
                        eq.status.upper() if eq.status else None,
                        eq.plate_no if eq.plate_no else None,
                        eq.site.upper() if eq.site else None,
                        eq.color.upper() if eq.color else None,
                        eq.chasis_no.upper() if eq.chasis_no else None,
                        eq.brand_name.upper() if eq.brand_name else None,
                        eq.model if eq.model else None,
                        eq.last_inspection if eq.last_inspection else None,
                        eq.last_registration if eq.last_registration else None,
                        eq.next_registration if eq.next_registration else None,
                        eq.last_conduct_of_pm if eq.last_conduct_of_pm else None,
                        eq.next_pm if eq.next_pm else None,
                        wsd if wsd else srv,
                        d, s, r,
                        self.format_list_field(eq.problems_encountered) if eq.problems_encountered else "N/A",
                        eq.materials_purchased.upper() if eq.materials_purchased else "N/A",
                        qty_val,
                        mechanic_val,
                        remarks_val
                    ])

            final_rows = raw_rows

            # Sort by the equipment field
            final_rows.sort(key=lambda x: x[0], reverse=False)

            formatters = {
                9: lambda d: d.strftime('%d-%b-%Y') if isinstance(d, (date, datetime)) else d,
                10: lambda d: d.strftime('%d-%b-%Y') if isinstance(d, (date, datetime)) else d,
                11: lambda d: d.strftime('%d-%b-%Y') if isinstance(d, (date, datetime)) else d,
                12: lambda d: d.strftime('%d-%b-%Y') if isinstance(d, (date, datetime)) else d,
                13: lambda d: d.strftime('%d-%b-%Y') if isinstance(d, (date, datetime)) else d,
                15: lambda d: d.strftime('%d-%b-%Y') if isinstance(d, (date, datetime)) else d
            }

            return export_to_excel(
                headers=header,
                file_name="master_list_equipments_",
                queryset=final_rows,
                formatters=formatters,
                title="Equipments"
            )

        except Exception as e:
            return response_message_utils(
                message=f"Something went wrong while exporting your excel {e} 13123123",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

# MASTER LIST IMPORT AND EXPORT V3

class MasterListEquipmentV3ExportView(generics.ListAPIView):

    permission_classes = [IsAuthenticated, AllRoles]

    def once_displayed(self, queryset, fields):

        field_counters = {f: Counter() for f in fields}

        for eq in queryset:
            for f in fields:
                value = getattr(eq, f, None)

                if value:
                    field_counters[f][value] += 1

        # Track which values have been displayed
        displayed_fields = {f: set() for f in fields}


        def display(field_name, value):
            if not value:
                return None
            counts = field_counters[field_name]
            displayed = displayed_fields[field_name]

            if counts[value] == 1:  # only appears once in all queryset
                return value
            if value not in displayed:
                displayed.add(value)
                return value
            return None  # duplicate after first display

        return display
    
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
            equipment_nos = self.request.data.get('equipment_nos')

            if not Equipment.objects.filter(equipment_no__in=equipment_nos).exists():
                return response_message_utils(
                    message="No equipment no found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            # Header Row
            header = [
                "EQUIPMENT",
                "EQUIPMENT NO.",
                "STATUS",
                "PLATE NO",
                "SITE",
                "COLOR",
                "CHASIS NO",
                "BRAND NAME",
                "MODEL",
                "LAST INSPECTION",
                "LAST REGISTRATION",
                "NEXT REGISTRATION",
                "LAST CONDUCT OF PM",
                "NEXT PM",
                "SERVICE RENDERED",
                "PROBLEMS ENCOUNTERED",
                "MATERIALS PURCHASED",
                "QUANTITY",
                "MECHANIC",
                "REMARKS"
            ]

            equipment = (
                Equipment.objects
                .order_by('created_at')
                .filter(
                    equipment_no__in=equipment_nos,
                    status=EquipmentStatus.ACTIVE,
                    is_created_equipment=True
                )
            )

            raw_rows = []

            # Iterate over the original equipments
            for orig_eq in equipment:
                
                raw_rows.append([
                    orig_eq.equipment.upper() if orig_eq.equipment else None,
                    orig_eq.equipment_no if orig_eq.equipment_no else None,
                    orig_eq.status.upper() if orig_eq.status else None,
                    orig_eq.plate_no if orig_eq.plate_no else None,
                    orig_eq.site.upper() if orig_eq.site else None,
                    orig_eq.color.upper() if orig_eq.color else None,
                    orig_eq.chasis_no.upper() if orig_eq.chasis_no else None,
                    orig_eq.brand_name.upper() if orig_eq.brand_name else None,
                    orig_eq.model if orig_eq.model else None,
                    orig_eq.last_inspection if orig_eq.last_inspection else None,
                    orig_eq.last_registration if orig_eq.last_registration else None,
                    orig_eq.next_registration if orig_eq.next_registration else None,
                    orig_eq.last_conduct_of_pm if orig_eq.last_conduct_of_pm else None,
                    orig_eq.next_pm if orig_eq.next_pm else None,
                    self.format_list_field(orig_eq.service_rendered),
                    self.format_list_field(orig_eq.problems_encountered),
                    orig_eq.materials_purchased.upper() if orig_eq.materials_purchased else "N/A",
                    orig_eq.quantity if orig_eq.quantity else 0,
                    orig_eq.mechanic.upper() if orig_eq.mechanic else "N/A",
                    orig_eq.remarks.upper() if orig_eq.remarks else "N/A",
                ])
                
                final_rows = raw_rows

                # Sort by the equipment field
                final_rows.sort(key=lambda x: x[0], reverse=False)

                formatters = {
                    9: lambda d: d.strftime('%d-%b-%Y') if isinstance(d, (date, datetime)) else d,
                    10: lambda d: d.strftime('%d-%b-%Y') if isinstance(d, (date, datetime)) else d,
                    11: lambda d: d.strftime('%d-%b-%Y') if isinstance(d, (date, datetime)) else d,
                    12: lambda d: d.strftime('%d-%b-%Y') if isinstance(d, (date, datetime)) else d,
                    13: lambda d: d.strftime('%d-%b-%Y') if isinstance(d, (date, datetime)) else d,
                }

            if len(raw_rows) == 0 or len(final_rows) == 0:
                return response_message_utils(
                    message=f"No data found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            return export_to_excel(
                headers=header,
                file_name="master_list_equipments_",
                queryset=final_rows,
                formatters=formatters,
                title="Equipments"
            )

        except Exception as e:
            return response_message_utils(
                message=f"Something went wrong while exporting your excel {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MasterListEquipmentV3ImportView(BaseImportView):

    serializer_class = ImportxlsxInMasterListEquipmentsV3Serializer

    queryset = Equipment.objects.all()

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
        
# MASTERLIST IMPORT AND EXPORT

class MasterListEquipmentV2Views(BaseFeatureViewSet):

    model = Equipment

    item_to_search = ["equipment"]

    def list(self, request, *args, **kwargs):

        queryset = self.get_queryset().order_by('-updated_at')

        merged = OrderedDict()

        for row in queryset:

            key = row.equipment_no

            # If the key not present in merged get the data in that specific key
            if key not in merged:
                merged[key] = {
                    "id": row.id,
                    "equipment_no": row.equipment_no,
                    "equipment": row.equipment.upper() if row.equipment else None,
                    "plate_no": row.plate_no,
                    "chasis_no": row.chasis_no,
                    "model": row.model,
                    "status": row.status
                }
            else:
                # If the key already present 
                target = merged[key]
                for field in ["id", "equipment_no", "equipment", "plate_no",
                              "chasis_no", "model", "status"]:

                    new_value = getattr(row, field)

                    if not target[field] and new_value:
                        target[field] = new_value

        # Convert the dict to list
        merged_list = list(merged.values())

        page = self.paginate_queryset(merged_list)

        if page is not None:
            return self.get_paginated_response(page)

    serializer_action_classes = {   
        "create": CreateEquipmentV2Serializer,
        "list": ListEquipmentV2Serializer,
        "retrieve": ListEquipmentDetailsV2Serializer,
        "update": UpdateMasterlistEquipmentV2Serializer,
        "partial_update": UpdateMasterlistEquipmentV2Serializer
    }

    @action(detail=False, methods=["delete"], url_path='bulk')
    def bulk_delete(self, request, *args, **kwargs):
        """
        Handles bulk delete
        """
        ids_or_no = request.data.get("ids_or_no", [])

        if not isinstance(ids_or_no, list) or len(ids_or_no) < 1:
            return response_message_utils(
                message="ids_or_no` must be a non-empty list.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        representative_equipment = self.model.objects.filter(id__in=ids_or_no).order_by('created_at')

        if not representative_equipment:
            return response_message_utils(
                message=getattr(self, "not_found_message", "No equipment id found."),
                status_code=status.HTTP_404_NOT_FOUND
            )

        for instance in representative_equipment:
            if hasattr(self, "log_activity"):
                self.log_activity(request, instance)

        for repr in representative_equipment:

            queryset = self.model.objects.filter(
                equipment_no__iexact=repr.equipment_no
            )

            queryset.delete()

        return response_message_utils(
            message=getattr(self, "success_bulk_delete_message", "Successfully bulk deleted."),
            status_code=status.HTTP_200_OK
        )

    success_create_message = "Successfully create equipment"
    success_delete_message = "Succesfully deleted the equipment"
    not_found_message = "No equipment id found"
    success_update_message = "Successfully update the equipment"


    def retrieve(self, request, *args, **kwargs):
        
        instance = Equipment.objects.filter(id=kwargs.get("id")).first()

        serializer = self.get_serializer(instance)

        return Response(serializer.data)




class MasterListEquipmentDetailsV2Views(generics.GenericAPIView, mixins.RetrieveModelMixin):

    serializer_class = ListGroupEquipmentDetailsV2Serializer
    permission_classes = [IsAuthenticated]

    lookup_field = 'id'
    lookup_url_kwarg = 'id'

    def get_queryset(self):
        return Equipment.objects.all()
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["id"] = self.kwargs.get('id')
        return context

    def get(self, request, *args, **kwargs):

        serializer = self.retrieve(request, *args, **kwargs)

        return response_message_utils(
            message="List of group equipment details",
            data=serializer.data,
            status_code=200
        )


class MasterListExistingToolsEquipmentViews(generics.GenericAPIView, mixins.ListModelMixin):

    permission_classes = [IsAuthenticated]
    serializer_class = DropdownItemEquipmentSerializer

    def get_queryset(self):
        return Equipment.objects.values('equipment', 'equipment_no').distinct()
    

    def get(self, request, *args, **kwargs):

        serializer = self.get_serializer(self.get_queryset(), many=True)

        return response_message_utils(
            message="List of existing equipments",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
    

class MasterListExistingEquipmentNumberViews(generics.GenericAPIView, mixins.ListModelMixin):

    permission_classes = [IsAuthenticated]
    serializer_class = DropdownSerialEquipmentNumberSerializer

    def get_queryset(self):
        return Equipment.objects.values('equipment_no').distinct()
    
    def get(self, request, *args, **kwargs):

        serializer = self.get_serializer(self.get_queryset(), many=True)

        return response_message_utils(
            message="List of existing serial equipment no",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

class EquipmentLookupViews(generics.GenericAPIView, mixins.RetrieveModelMixin):

    permission_classes = [IsAuthenticated]
    serializer_class = EquipmentLookupSerializer
    lookup_field = 'equipment_no'
    lookup_url_kwarg = 'equipment_no'

    def get_queryset(self):
        return Equipment.objects.filter(equipment_no__iexact=self.kwargs.get(self.lookup_field))
    

    def get(self, request, *args, **kwargs):

        equipment = self.get_queryset().first()

        if not equipment:
            return response_message_utils(
                message="No equipment no found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(equipment, many=False)

        return response_message_utils(
            message="Equipment found",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    

