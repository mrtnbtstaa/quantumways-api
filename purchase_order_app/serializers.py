from rest_framework import serializers
from .models import PurchaseOrder, PurchaseItem, PurchaseAdditionalInformation, PurchaseProject, PurchaseVendee
from quantumways.utils import is_field_empty, is_valid_input_int, raise_validation, CustomCharField, CustomIntegerField, CustomDecimalField, CustomBooleanField, decode_base64_image_from_csv
from quantumways.utils import Base64ImageField
# from quantumways.constants import RequestStatus
import csv
from io import TextIOWrapper
from quantumways.services.services import create_bulk_items
from collections import defaultdict
import base64
from django.db import transaction
from django.core.files.base import ContentFile
import uuid
from math import ceil
from PIL import Image, ImageFile
from io import BytesIO
from openpyxl import load_workbook
from decimal import Decimal
from django.db.models import Sum
from datetime import datetime, date
from master_list_app.models import Supplier, Product

class AddPurchaseItemsInTopManagementSerializer(serializers.ModelSerializer):

    quantity = CustomIntegerField(
        blank_message="Quantity cannot be blank",
        required_message="Quantity is required"
    )
    description = CustomCharField(
        blank_message="Description cannot be blank",
        required_message="Description is required"
    )
    unit_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        error_messages={
            "blank": "Unit price cannot be blank",
            "null": "Unit price cannot have null value",
            "invalid": "Invalid unit price value"
        }
    )
    unit = CustomCharField(
        blank_message="Unit cannot be blank",
        required_message="Unit is required"
    )
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        error_messages={
            "blank": "Amount cannot be blank",
            "null": "Amout cannot have null value",
            "invalid": "Invalid amount value"
        }
    )
    

    class Meta:
        model = PurchaseItem
        fields = ['quantity', 'description', 'unit_price', 'unit', 'amount']


    def validate(self, attrs):

        quantity = attrs["quantity"]
        unit_price = attrs["unit_price"]
        amount = attrs["amount"]

        if quantity < 0:
            raise_validation("Quantity must be positive value")
            
        if is_field_empty(attrs["description"]):
            raise_validation("Description cannot be blank")

        if not Product.objects.filter(item__icontains=attrs["description"]).exists():
            raise_validation("No description found")

        if unit_price < 0:
            raise_validation("Unit price must be positive value")

        if is_field_empty(attrs["unit"]):
            raise_validation("Unit cannot be blank")

        if amount < 0:
            raise_validation("Amount must be positive value")


        return attrs
    
class AddPurchaseVendeeInTopManagementSerializer(serializers.ModelSerializer):

    company_name = CustomCharField(
        blank_message="Company name cannot be blank",
        required_message="Company name is required"
    )
    address = CustomCharField(
        blank_message="Address cannot be blank",
        required_message="Address is required"
    )
    contact_person = CustomCharField(
        blank_message="Contact person cannot be blank",
        required_message="Contact person is required"
    )
    phone_email = CustomCharField(
        blank_message="Phone or email cannot be blank",
        required_message="Phone or email is required"
    )
   
    class Meta:
        model = PurchaseVendee
        fields = ['company_name', 'address', 'contact_person', 'phone_email']


    def validate(self, attrs):

        if is_field_empty(attrs["company_name"]):
            raise_validation("Company name cannot be blank")

        if not Supplier.objects.filter(item__icontains=attrs["company_name"]).exists():
            raise_validation("No Company name found")

        if is_field_empty(attrs["address"]):
            raise_validation("Address cannot be blank")
        
        if is_field_empty(attrs["contact_person"]):
            raise_validation("Contact person cannot be blank")

        if is_field_empty(attrs["phone_email"]):
            raise_validation("Phone or email cannot be blank")

        return attrs
    
class AddPurchaseProjectInTopManagementSerializer(serializers.ModelSerializer):

    project_name = CustomCharField(
        blank_message="Project name cannot be blank",
        required_message="Project name is required"
    )
    address = CustomCharField(
        blank_message="Address cannot be blank",
        required_message="Address is required"
    )
    contact_person = CustomCharField(
        blank_message="Contact person cannot be blank",
        required_message="Contact person is required"
    )
    phone_email = CustomCharField(
        blank_message="Phone or email cannot be blank",
        required_message="Phone or email is required"
    )
   
    class Meta:
        model = PurchaseProject
        fields = ['project_name', 'address', 'contact_person', 'phone_email']


    def validate(self, attrs):

        if is_field_empty(attrs["project_name"]):
            raise_validation("Project name cannot be blank")

        if is_field_empty(attrs["address"]):
            raise_validation("Address cannot be blank")
        
        if is_field_empty(attrs["contact_person"]):
            raise_validation("Contact person cannot be blank")

        if is_field_empty(attrs["phone_email"]):
            raise_validation("Phone or email cannot be blank")

        return attrs

class AddPurchaseAdditionalInformationInTopManagementSerializer(serializers.ModelSerializer):

    for_delivery = serializers.BooleanField(
        error_messages={
            "null": "For delivery cannot have null value",
            "invalid": "Invalid for delivery value"
        }
    ) 

    for_pick_up_by = serializers.BooleanField(
        error_messages={
            "null": "For pick up by cannot have null value",
            "invalid": "Invalid for pick up by value"
        }
    )

    for_pick_up_by_text = CustomCharField(
        blank_message="For pick up by cannot be blank",
        required_message="For pick up by is required",
        allow_null=True,
        allow_blank=True
    )

    remarks = CustomCharField(
        blank_message="Remarks cannot be blank",
        required_message="Remarks is required"
    )

   
    class Meta:
        model = PurchaseAdditionalInformation
        fields = ['for_delivery', 'for_pick_up_by', 'for_pick_up_by_text', 'remarks']


    def validate(self, attrs):

        if attrs.get('for_delivery', False) is None:
            raise_validation("For delivery cannot be blank")

        if attrs.get("for_pick_up_by", None) is None and is_field_empty(attrs.get('for_pick_up_by_text', None)):
            raise_validation("For pick up by cannot be blank")

        if is_field_empty(attrs["remarks"]):
            raise_validation("Remarks cannot be blank")

        return attrs


class AddPurchaseOrderInTopManagementSerializer(serializers.ModelSerializer):


    po_control_no = CustomCharField(
        None,
        None,
        required=False,
        allow_blank=True
    )
    document_revisions = CustomCharField(
        blank_message="Document revisions cannot be blank",
        required_message="Document revisions is required"
    )
    pr_no = CustomCharField(
        blank_message="Pr number cannot be blank",
        required_message="Pr number is required"
    )
    po_date = serializers.DateField(
        error_messages={
            "null": "Po Date cannot be blank",
            "invalid": "Po Date must use this format: MM/DD/YY"
        },
        input_formats=['%m/%d/%y']
    )
    cash_payment = serializers.BooleanField(
        error_messages={
            "null": "Cash payment cannot have null value",
            "invalid": "Invalid cash payment value"
        }
    )

    cheque_payment = serializers.BooleanField(
        error_messages={
            "null": "Cheque payment cannot have null value",
            "invalid": "Invalid cheque payment value"
        }
    )

    vendee = AddPurchaseVendeeInTopManagementSerializer()
    project = AddPurchaseProjectInTopManagementSerializer()
    additional_information = AddPurchaseAdditionalInformationInTopManagementSerializer()
    items = AddPurchaseItemsInTopManagementSerializer(many=True)
   
    class Meta:
        model = PurchaseOrder
        fields = ['po_control_no', 'document_revisions', 'pr_no', 'po_date', 'cash_payment', 'cheque_payment', 'po_date', 'vendee', 'project', 'additional_information', 'items']

    def to_internal_value(self, data):

        if data["po_date"] in (None, "") or data["po_date"].strip() == "":
            raise_validation("Po date cannot be blank")

        return super().to_internal_value(data)

    def validate(self, attrs):

        if not str(attrs["po_control_no"]).startswith("F-") and attrs["po_control_no"]:
            raise_validation("PO Control No must always start with F-")

        if not str(attrs["pr_no"]).startswith("F-"):
            raise_validation("PR No must always start with F-")

        if PurchaseOrder.objects.filter(po_control_no=attrs["po_control_no"]).exists():
            raise_validation(f"PO Control No: {attrs["po_control_no"]} already exists")

        if PurchaseOrder.objects.filter(pr_no=attrs["pr_no"]).exists():
            raise_validation(f"PR No: {attrs["pr_no"]} already exists")


        if is_field_empty(attrs["pr_no"]):
            raise_validation("Pr number cannot be blank")

        if is_field_empty(attrs["document_revisions"]):
            raise_validation("Document revisions cannot be blank")

        return attrs
    
    def create(self, validated_data):
        
        # Extract the nested serializers data
        purchase_vendee_data = validated_data.pop('vendee')
        purchase_project_data = validated_data.pop('project')
        purchase_additional_information_data = validated_data.pop('additional_information')
        purchase_items_data = validated_data.pop('items')


        with transaction.atomic():

            try:
                
                # Create the purchase order associated with the purchase items
                purchase_order = create_bulk_items(
                    main_model=PurchaseOrder,
                    child_model=PurchaseItem,
                    main_data=validated_data,
                    children_data=purchase_items_data,
                    foreign_key_name='purchase_order'
                )

                total = purchase_order.items.aggregate(total=Sum('amount'))['total'] or 0
                purchase_order.total_amount = total
                purchase_order.save(update_fields=['total_amount'])

                # Create the purchase vendee
                purchase_vendee = PurchaseVendee.objects.create(purchase_order=purchase_order, **purchase_vendee_data)

                # Create the purchase project
                purchase_project = PurchaseProject.objects.create(purchase_order=purchase_order, **purchase_project_data)

                # Create the purchase additional information
                purchase_additional_information = PurchaseAdditionalInformation.objects.create(purchase_order=purchase_order, **purchase_additional_information_data)

                return purchase_order


            except Exception as e:
                raise_validation("Something went wrong when creating the data")

class ImportXlxsInPurchaseOrdersSerializer(serializers.Serializer):

    excel_file = serializers.FileField()

    @staticmethod
    def str_to_bool(val):
        return str(val).strip().upper() == "TRUE"

    def validate(self, attrs):
        file = attrs.get("excel_file")
        if not file.name.endswith('.xlsx'):
            raise serializers.ValidationError("Only Excel files are allowed.")
        return attrs
    

    def create(self, validated_data):
        excel_file = validated_data["excel_file"]
        wb = load_workbook(filename=BytesIO(excel_file.read()), data_only=True)
        sheet = wb.active
        grouped_data = defaultdict(list)
        failed_imports = []
        created_orders = []


        headers = [cell.value for cell in sheet[1]]


        # Group the per rows
        for rows in sheet.iter_rows(min_row=2, values_only=True):

            row_dict = dict(zip(headers, rows))
            po_control_no = row_dict.get('PO Control No')
            if po_control_no:
                grouped_data[po_control_no].append(row_dict)

        # Process each group
        for pr_no, rows in grouped_data.items():
            try:

                first = rows[0]


                if not PurchaseOrder.objects.filter(po_control_no=first["PO Control No"]).exists():
                    pr_data = {
                        "po_control_no": first["PO Control No"],
                        "document_revisions": first["Document Revisions"],
                        "pr_no": first["PR Number"],
                        "po_date": datetime.strptime(first["PO Date"], '%m/%d/%y').date(),
                        "cash_payment": ImportXlxsInPurchaseOrdersSerializer.str_to_bool(first["Cash Payment"]),
                        "cheque_payment": ImportXlxsInPurchaseOrdersSerializer.str_to_bool(first["Cheque Payment"]),
                        "total_amount": 0
                    }
                

                    items_data = [
                        {
                            "quantity": row['Qty'],
                            "description": row['Description'],
                            "unit_price": row['Unit Price'],
                            "unit": row['Unit'],
                            "amount": row['Amount']
                        }
                        for row in rows
                    ]

                    purchase_order = create_bulk_items(
                        main_model=PurchaseOrder,
                        child_model=PurchaseItem,
                        main_data=pr_data,
                        children_data=items_data,
                        foreign_key_name='purchase_order'
                    )

                    total = purchase_order.items.aggregate(total=Sum('amount'))['total'] or 0
                    purchase_order.total_amount = total
                    purchase_order.save(update_fields=['total_amount'])

                    PurchaseVendee.objects.create(
                        purchase_order=purchase_order,
                        company_name=first["Company Name"],
                        address=first["Address"],
                        contact_person=first["Contact Person"],
                        phone_email=first["Phone/Email"]
                    )

                    PurchaseProject.objects.create(
                        purchase_order=purchase_order,
                        project_name=first["Project Name"],
                        address=first["Address"],
                        contact_person=first["Contact Person"],
                        phone_email=first["Phone/Email"]
                    )

                    PurchaseAdditionalInformation.objects.create(
                        purchase_order=purchase_order,
                        for_delivery=ImportXlxsInPurchaseOrdersSerializer.str_to_bool(first.get("For Delivery", False)),
                        for_pick_up_by=first.get("For pick up by", ""),
                        for_pick_up_by_text=first.get("For pick up by text", ""),
                        remarks=first["Remarks"]
                    )


                    created_orders.append(purchase_order)
                else:
                    continue

            except Exception as e:
                failed_imports.append({
                    "pr_no": pr_no,
                    "error": str(e)
                })

        if failed_imports:
            raise serializers.ValidationError({
                "message": "Some rows failed to import.",
                "failures": failed_imports
            })
        
        return created_orders




class ViewPurchaseOrderInTopManagementSerializer(serializers.ModelSerializer):
    purchase_order_id = serializers.UUIDField(source='id')
    class Meta:
        model = PurchaseOrder
        fields = ['purchase_order_id', 'po_control_no', 'po_date', 'pr_no']


class SearchPurchaseOrderInTopManagementSerializer(serializers.ModelSerializer):
    purchase_order_id = serializers.UUIDField(source='id')
    class Meta:
        model = PurchaseOrder
        fields = ['purchase_order_id', 'po_control_no', 'po_date', 'pr_no']


class ViewPurchaseVendeeDetailsInTopManagementSerializer(serializers.ModelSerializer):

    purchase_vendee_id = serializers.UUIDField(source='id')

    class Meta:
        model = PurchaseVendee
        fields = ['purchase_vendee_id', 'company_name', 'address', 'contact_person', 'phone_email']

class ViewPurchaseProjectDetailsInTopManagementSerializer(serializers.ModelSerializer):

    purchase_project_id = serializers.UUIDField(source='id')

    class Meta:
        model = PurchaseProject
        fields = ['purchase_project_id', 'project_name', 'address', 'contact_person', 'phone_email']

class ViewPurchaseAdditionalInformationDetailsInTopManagementSerializer(serializers.ModelSerializer):

    purchase_additional_info_id = serializers.UUIDField(source='id')

    class Meta:
        model = PurchaseAdditionalInformation
        fields = ['purchase_additional_info_id', 'for_delivery', 'for_pick_up_by', 'for_pick_up_by_text', 'remarks']

class ViewPurchaseItemsDetailsInTopManagementSerializer(serializers.ModelSerializer):

    purchase_item_id = serializers.UUIDField(source='id')
    amount = CustomDecimalField(max_digits=12, decimal_places=2)

    class Meta:
        model = PurchaseItem
        fields = ['purchase_item_id', 'quantity', 'description', 'unit_price', 'unit', 'amount']

class ViewPurchaseOrderDetailsInTopManagementSerializer(serializers.ModelSerializer):
    
    purchase_order_id = serializers.UUIDField(source='id')
    vendee = ViewPurchaseVendeeDetailsInTopManagementSerializer()
    project = ViewPurchaseProjectDetailsInTopManagementSerializer()
    additional_information = ViewPurchaseAdditionalInformationDetailsInTopManagementSerializer()
    items = ViewPurchaseItemsDetailsInTopManagementSerializer(many=True)
    total_amount = CustomDecimalField(max_digits=12, decimal_places=2)
    po_date = serializers.DateField(format='%m/%d/%y', input_formats=['%m/%d/%y'])
    class Meta:
        model = PurchaseOrder
        fields = [
            'purchase_order_id' ,'pr_no', 'document_revisions', 'cash_payment',
            'cheque_payment', 'total_amount', 'po_date', 'vendee', 'project',
            'additional_information', 'items'
        ]


class UpdatePurchaseVendeeSerializer(serializers.ModelSerializer):
    purchase_vendee_id = CustomCharField(
        source="id",
        blank_message="Id must be present to update the purchase items",
        required_message="Id is required"
    )
    company_name = CustomCharField(
        blank_message="Company name cannot be blank",
        required_message="Company name is required"
    )
    address = CustomCharField(
        blank_message="Address cannot be blank",
        required_message="Address is required"
    )
    contact_person = CustomCharField(
        blank_message="Contact person cannot be blank",
        required_message="Contact person is required"
    )
    phone_email = CustomCharField(
        blank_message="Phone or email cannot be blank",
        required_message="Phone or email is required",
    )
    

    class Meta:
        model = PurchaseVendee
        fields = ['purchase_vendee_id', 'company_name', 'address', 'contact_person', 'phone_email']

    def validate(self, attrs):

        if is_field_empty(attrs["id"]):
            raise_validation("Id must be present to update the purchase items")

        if is_field_empty(attrs["company_name"]):
            raise_validation("Company name cannot be blank")

        if is_field_empty(attrs["address"]):
            raise_validation("Address cannot be blank")

        if is_field_empty(attrs["contact_person"]):
            raise_validation("Contact person cannot be blank")

        if is_field_empty(attrs["phone_email"]):
            raise_validation("Phone or email cannot be blank")

        return attrs
    
class UpdatePurchaseProjectSerializer(serializers.ModelSerializer):

    purchase_project_id  = CustomCharField(
        blank_message="Id must be present to update the purchase items",
        required_message="Id is required",
        source='id'
    )
    project_name = CustomCharField(
        blank_message="Project name cannot be blank",
        required_message="Project name is required"
    )
    address = CustomCharField(
        blank_message="Address cannot be blank",
        required_message="Address is required"
    )
    contact_person = CustomCharField(
        blank_message="Contact person cannot be blank",
        required_message="Contact person is required"
    )
    phone_email = CustomCharField(
        blank_message="Phone or email cannot be blank",
        required_message="Phone or email is required",
    )
    
    class Meta:
        model = PurchaseProject
        fields = ['purchase_project_id', 'project_name', 'address', 'contact_person', 'phone_email']

    def validate(self, attrs):

        if is_field_empty(attrs["id"]):
            raise_validation("Purchase Project ID is required for updating")

        if is_field_empty(attrs["project_name"]):
            raise_validation("Project name cannot be blank")

        if is_field_empty(attrs["address"]):
            raise_validation("Address cannot be blank")

        if is_field_empty(attrs["contact_person"]):
            raise_validation("Contact person cannot be blank")

        if is_field_empty(attrs["phone_email"]):
            raise_validation("Phone or email cannot be blank")

        return attrs


class UpdatePurchaseAdditionalInformationSerializer(serializers.ModelSerializer):

    purchase_additional_info_id = CustomCharField(
        blank_message="Id must be present to update the purchase items",
        required_message="Id is required",
        source="id"
    )
    for_delivery = serializers.BooleanField(
        error_messages={
            "null": "For delivery cannot have null value",
            "invalid": "Invalid for delivery value"
        }
    ) 

    for_pick_up_by = serializers.BooleanField(
        error_messages={
            "null": "For pick up by cannot have null value",
            "invalid": "Invalid for pick up by value"
        }
    )

    for_pick_up_by_text = CustomCharField(
        blank_message="For pick up by cannot be blank",
        required_message="For pick up by is required",
        allow_null=True,
        allow_blank=True
    )
    remarks = CustomCharField(
        blank_message="Remarks cannot be blank",
        required_message="Remarks is required"
    )


    class Meta:
        model = PurchaseAdditionalInformation
        fields = ['purchase_additional_info_id', 'for_delivery', 'for_pick_up_by', 'for_pick_up_by_text', 'remarks']

    def validate(self, attrs):

        if is_field_empty(attrs["id"]):
            raise_validation("Id must be present to update the purchase items")

        if attrs.get('for_delivery', False) is None:
            raise_validation("For delivery cannot be blank")

        if attrs.get("for_pick_up_by", None) is None and is_field_empty(attrs.get('for_pick_up_by_text', None)):
            raise_validation("For pick up by cannot be blank")

        if is_field_empty(attrs["remarks"]):
            raise_validation("Remarks cannot be blank")

        return attrs
    
class UpdatePurchaseItemsSerializer(serializers.ModelSerializer):

    purchase_item_id = CustomCharField(
        blank_message="Id must be present to update the purchase items",
        required_message="Id is required",
    )
    quantity = CustomIntegerField(
        blank_message="Quantity cannot be blank",
        required_message="Quantity is required"
    )
    description = CustomCharField(
        blank_message="Description cannot be blank",
        required_message="Description is required"
    )
    unit_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        error_messages={
            "blank": "Unit price cannot be blank",
            "null": "Unit price cannot have null value",
            "invalid": "Invalid unit price value"
        }
    )
    unit = CustomCharField(
        blank_message="Unit cannot be blank",
        required_message="Unit is required"
    )
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        error_messages={
            "blank": "Amount cannot be blank",
            "null": "Amout cannot have null value",
            "invalid": "Invalid amount value"
        }
    )
    
    class Meta:
        model = PurchaseItem
        fields = ['purchase_item_id', 'quantity', 'description', 'unit_price', 'unit', 'amount']

    def validate(self, attrs):

        if is_field_empty(attrs["purchase_item_id"]):
            raise_validation("Id must be present to update the purchase items")

        if attrs["quantity"] is None:
            raise_validation("Quantity cannot be blank")

        if attrs["quantity"] < 0:
            raise_validation("Quantity must be positive value")

        if is_field_empty(attrs["description"]):
            raise_validation("Description cannot be blank")

        if attrs["unit_price"] < 0:
            raise_validation("Unit price must be positive value")

        if is_field_empty(attrs["unit"]):
            raise_validation("Unit cannot be blank")

        if attrs["amount"] is None:
            raise_validation("Amount cannot be blank")

        if attrs["amount"] < 0:
            raise_validation("Amount must be positive value")

        return attrs

class UpdatePurchaseOrderSerializer(serializers.ModelSerializer):

    document_revisions = CustomCharField(
        blank_message="Document revisions cannot be blank",
        required_message="Document revisions is required"
    )
    pr_no = CustomCharField(
        blank_message="PR No cannot be blank",
        required_message="PR No is required"
    )
    po_date = serializers.DateField(
        format='%m/%d/%y', input_formats=['%m/%d/%y'],
        error_messages={
            "blank": "PO Date cannot be blank",
            "invalid": "PO Date must use this format: MM/DD/YY"
        }
    )
    cash_payment = serializers.BooleanField(
        error_messages={
            "null": "Cash payment cannot have null value",
            "invalid": "Invalid cash payment value"
        }
    )

    cheque_payment = serializers.BooleanField(
        error_messages={
            "null": "Cheque payment cannot have null value",
            "invalid": "Invalid cheque payment value"
        }
    )
    vendee = UpdatePurchaseVendeeSerializer()
    project = UpdatePurchaseProjectSerializer()
    additional_information = UpdatePurchaseAdditionalInformationSerializer()
    items = UpdatePurchaseItemsSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            'po_control_no', 'document_revisions', 'pr_no',
            'cash_payment', 'cheque_payment', 'po_date',
            'vendee', 'project', 'additional_information',
            'items'
        ]


    def to_internal_value(self, data):

        po_date = data.get('po_date')

        if po_date in (None, "") or str(po_date).strip() == "":
            raise_validation("PO Date cannot be blank")

        return super().to_internal_value(data)

    def validate(self, attrs):

        if is_field_empty(attrs["document_revisions"]):
            raise_validation("Document revisions cannot be blank")

        if is_field_empty(attrs["pr_no"]):
            raise_validation("Pr No cannot be blank")

        return attrs
    
    def update(self, instance, validated_data): 

        # Extract the nested data items
        vendee_data = validated_data.pop('vendee')
        project_data = validated_data.pop('project')
        additional_information_data = validated_data.pop('additional_information')
        items_data = validated_data.pop('items')

        # Updating purchase order
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Updating purchase vendee
        for attr, value in vendee_data.items():
            setattr(instance.vendee, attr, value)
        instance.vendee.save()


        # Updating purchase project
        for attr, value in project_data.items():
            setattr(instance.project, attr, value)
        instance.project.save()

        # Updating purchase additional information 
        for attr, value in additional_information_data.items():
            setattr(instance.additional_information, attr, value)
        instance.additional_information.save()


        # Convert keys to string for comparison
        existing_items = {str(item.id): item for item in instance.items.all()}
        # Update existing delivery items
        for item_data in items_data:
            item_id = str(item_data.get("purchase_item_id"))

            if item_id and item_id in existing_items:
                item_instance = existing_items[item_id]

                for attr, value in item_data.items():
                    setattr(item_instance, attr, value)

                item_instance.save()

        total = instance.items.aggregate(total=Sum('amount'))['total'] or 0
        instance.total_amount = total
        instance.save(update_fields=['total_amount'])

        return instance