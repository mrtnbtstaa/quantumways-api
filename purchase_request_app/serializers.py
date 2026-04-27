from rest_framework import serializers
from .models import PurchaseItem, PurchaseRequest
from quantumways.utils import is_field_empty, raise_validation, CustomCharField
from quantumways.utils import Base64ImageField
from quantumways.constants import RequestStatus
from quantumways.services.services import create_bulk_items
from collections import defaultdict
from datetime import datetime
from io import BytesIO
from master_list_app.models import Product
from openpyxl import load_workbook

class AddPurchaseItemsInTopManagementSerializer(serializers.ModelSerializer):
    no = serializers.IntegerField(
        error_messages={
            "blank": "No cannot be blank",
            "null": "No cannot have null value",
            "invalid": "Invalid no value"
        }
    )
    quantity = serializers.IntegerField(
        error_messages={
            "blank": "Quantity cannot be blank",
            "null": "Quantity cannot have null values",
            "invalid": "Invalid quantity values"
        }
    )
    unit = CustomCharField(
        blank_message="Unit cannot be blank",
        required_message="Unit is required"
    )
    description = CustomCharField(
        blank_message="Description cannot be blank",
        required_message="Description is required"
    )
    purpose = CustomCharField(
        blank_message="Purpose cannot be blank",
        required_message="Purpose is required"
    )
    

    class Meta:
        model = PurchaseItem
        fields = ['no', 'quantity', 'unit', 'description', 'purpose']


    def validate(self, attrs):

        if attrs["no"] is None:
            raise_validation("No cannot be blank")

        if attrs["no"] < 0:
            raise_validation("No must be positive value")

        quantity = attrs["quantity"]

        if quantity is None:
            raise_validation("Quantity cannot be blank")

        if quantity < 0:
            raise_validation("Quantity must be positive value")

        if is_field_empty(attrs["unit"]):
            raise_validation("Unit cannot be blank")

        if is_field_empty(attrs["description"]):
            raise_validation("Description cannot be blank")

        if is_field_empty(attrs["purpose"]):
            raise_validation("Purpose cannot be blank")

        return attrs


class ImportXlslInPurchaseRequestSerializer(serializers.Serializer):

    excel_file = serializers.FileField()

    def validate(self, attrs):
        file = attrs.get("excel_file")
        if not file.name.endswith('.xlsx'):
            raise serializers.ValidationError("Only Excel files are allowed.")
        return attrs

    def create(self, validated_data):

        excel_file = validated_data["excel_file"]
        wb = load_workbook(filename=BytesIO(excel_file.read()), data_only=True)
        sheet = wb.active

        # Extract the headers
        headers = [cell.value for cell in sheet[1]]

        grouped_data = defaultdict(list)
        failed_imports = []
        created_request = []


        for row in sheet.iter_rows(min_row=2, values_only=True):
            row_dict = dict(zip(headers, row))
            pr_no = row_dict.get("PR No")
            if pr_no:
                grouped_data[pr_no].append(row_dict)


        # Process each group
        for pr_no, rows in grouped_data.items():

            try:

                first = rows[0]

                if not PurchaseRequest.objects.filter(pr_no=first["PR No"]).exists():
                    
                    pr_data = {
                        "pr_no": f"00{first['PR No']}",
                        "document_revisions": first["Document Revisions"],
                        "date_requested": first["Date Requested"],
                        "date_needed": first["Date Needed"],
                        "project_name": first['Project Name'],
                        "location": first['Location'],
                        "prepared_by": first['Prepared By'],
                        "requested_signature": first.get('Requested Signature'),
                        "remarks": first.get('Remarks'),
                        "approved_by": first.get('Approved By'),
                        "approved_signature": first.get('Approved Signature'),
                        "date_time": datetime.strptime(first["Date/Time"], '%m/%d/%Y').date(),
                        "request_status": first['Request Status'],
                        "final_remarks": first['Remarks']
                    }

                    items_data = [
                        {
                            "no": row["No"],
                            "quantity": row['Quantity'],
                            "unit": row['Unit'],
                            "description": row['Description'],
                            "purpose": row['Purpose']
                        }
                    for row in rows
                    ]

                    purchase_request = create_bulk_items(
                        main_model=PurchaseRequest,
                        child_model=PurchaseItem,
                        main_data=pr_data,
                        children_data=items_data,
                        foreign_key_name='purchase_request'
                    )

                    created_request.append(purchase_request)
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
            
        return created_request


class AddPurchaseRequestInTopManagementSerializer(serializers.ModelSerializer):

    document_revisions = CustomCharField(
        blank_message="Document revisions cannot be blank",
        required_message="Document revisions is required"
    )
    date_requested = serializers.DateField(
        input_formats=['%Y-%m-%d'],
        error_messages={"invalid": "Date requested must use this format: YYYY-MM-DD"}
    )
    date_needed = serializers.DateField(
        input_formats=['%Y-%m-%d'],
        error_messages={"invalid": "Date needed must use this format: YYYY-MM-DD"}
    )
    project_name = CustomCharField(
        blank_message="Project name cannot be blank",
        required_message="Project name is required"
    )
    location = CustomCharField(
        blank_message="Location name cannot be blank",
        required_message="Location name is required"
    )
    prepared_by = CustomCharField(
        blank_message="Prepared by cannot be blank",
        required_message="Prepared by is required"
    )
    requested_signature = Base64ImageField()
    remarks = CustomCharField(
        blank_message="Remarks cannot be blank",
        required_message="Remarks is required"
    )
    approved_by = CustomCharField(
        blank_message="Approved by cannot be blank",
        required_message="Approved by is required"
    )
    approved_signature = Base64ImageField()
    date_time = serializers.DateTimeField(
        input_formats=['%m/%d/%Y'],
        error_messages={"invalid": "Date time must use this format: MM/DD/YYYY"}
    )
    request_status = CustomCharField(
        blank_message="Request Status cannot be blank",
        required_message="Request status is required"
    )
    final_remarks = CustomCharField(
        blank_message="Remarks cannot be blank",
        required_message="Remarks is required"
    )
    purchase_items = AddPurchaseItemsInTopManagementSerializer(many=True)

    class Meta:
        model = PurchaseRequest
        fields = '__all__'

    def to_internal_value(self, data):
        
        if data["date_requested"] in (None, "") or data["date_requested"].strip() == "":
            raise_validation("Date requested cannot be blank")

        if data["date_needed"] in (None, "") or data["date_needed"].strip() == "":
            raise_validation("Date needed cannot be blank")

        if data["date_time"] in (None, "") or data["date_time"].strip() == "":
            raise_validation("Date time cannot be blank")

        return super().to_internal_value(data)

    def validate(self, attrs):

        if is_field_empty(attrs["document_revisions"]):
            raise_validation("Document revisions cannot be blank")

        allowed_status = RequestStatus.AVAILABLE_CHOICES

        if is_field_empty(attrs["project_name"]):
            raise_validation("Project name cannot be blank")

        if is_field_empty(attrs["location"]):
            raise_validation("Location cannot be blank")

        if is_field_empty(attrs["prepared_by"]):
            raise_validation("Prepared by cannot be blank")

        if is_field_empty(attrs["remarks"]):
            raise_validation("Remarks cannot be blank")

        if is_field_empty(attrs["approved_by"]):
            raise_validation("Approved by cannot be blank")

        if is_field_empty(attrs["request_status"]):
            raise_validation("Request status cannot be blank")

        if attrs["request_status"] not in allowed_status:
            raise_validation("Invalid request status")

        if is_field_empty(attrs["final_remarks"]):
            raise_validation("Remarks cannot be blank")
        
        return attrs
        

    def create(self, validated_data):
        
        items_data = validated_data.pop('purchase_items')

        purchase_request = create_bulk_items(
            main_model=PurchaseRequest,
            child_model=PurchaseItem,
            main_data=validated_data,
            children_data=items_data,
            foreign_key_name='purchase_request'
        )

        # items = purchase_request.purchase_items.all().order_by('id')

        # last_no = PurchaseItem.objects.aggregate(max_no=Max('no'))['max_no'] or 0

        # for item in items:
        #     last_no += 1
        #     item.no = last_no
        #     item.save(update_fields=['no'])

        return purchase_request



class ViewPurchaseRequestInTopManagementSerializer(serializers.ModelSerializer):

    purchase_request_id = serializers.UUIDField(source='id')

    class Meta:
        model = PurchaseRequest
        fields = ['purchase_request_id', 'pr_no', 'date_requested', 'date_needed']


class SearchPurchaseRequestInTopManagementSerializer(serializers.ModelSerializer):

    purchase_request_id = serializers.UUIDField(source='id')

    class Meta:
        model = PurchaseRequest
        fields = ['purchase_request_id', 'pr_no', 'date_requested', 'date_needed']


class ViewPurchaseItemsDetailsInTopManagementSerializer(serializers.ModelSerializer):

    purchase_item_id = serializers.UUIDField(source='id')

    class Meta:
        model = PurchaseItem
        fields = ['purchase_item_id', 'no', 'quantity', 'unit', 'description', 'purpose']

class ViewPurchaseRequestDetailsInTopManagementSerializer(serializers.ModelSerializer):
    
    purchase_request_id = serializers.UUIDField(source='id')
    purchase_items = ViewPurchaseItemsDetailsInTopManagementSerializer(many=True)

    class Meta:
        model = PurchaseRequest
        fields = [
            'purchase_request_id' ,'pr_no', 'document_revisions', 'date_requested',
            'date_needed', 'project_name', 'location',
            'prepared_by', 'requested_signature', 'remarks',
            'approved_by', 'approved_signature', 'date_time',
            'request_status', 'final_remarks', 'purchase_items'
        ]


class UpdatePurchaseItemsSerializer(serializers.ModelSerializer):
    purchase_item_id = CustomCharField(
        blank_message="Id must be present to update the purchase items",
        required_message="Purchase Item ID is required",
    )
    no = serializers.IntegerField(
        error_messages={
            "blank": "No cannot be blank",
            "null": "No cannot have null value",
            "invalid": "Invalid no value"
        }
    )
    quantity = serializers.IntegerField(
        error_messages={
            "blank": "Quantity cannot be blank",
            "null": "Quantity cannot have null values",
            "invalid": "Invalid quantity values"
        }
    )
    unit = CustomCharField(
        blank_message="Unit cannot be blank",
        required_message="Unit is required"
    )
    description = CustomCharField(
        blank_message="Description cannot be blank",
        required_message="Description is required"
    )
    purpose = CustomCharField(
        blank_message="Purpose cannot be blank",
        required_message="Purpose is required"
    )
    

    class Meta:
        model = PurchaseItem
        fields = ['purchase_item_id', 'no', 'quantity', 'unit', 'description', 'purpose']

    def validate(self, attrs):

        if is_field_empty(attrs["purchase_item_id"]):
            raise_validation("Purchase Item ID is required for updating")

        if attrs["no"] is None:
            raise_validation("No cannot be blank")

        if attrs["no"] < 0:
            raise_validation("No must be positive value")

        if attrs["quantity"] is None:
            raise_validation("Quantity cannot be blank")

        if attrs["quantity"] < 0:
            raise_validation("Quantity must be positive value")

        if is_field_empty(attrs["unit"]):
            raise_validation("Unit cannot be blank")

        if is_field_empty(attrs["description"]):
            raise_validation("Description cannot be blank")

        if is_field_empty(attrs["purpose"]):
            raise_validation("Puporse cannot be blank")

        return attrs

class UpdatePurchaseRequestSerializer(serializers.ModelSerializer):

    document_revisions = CustomCharField(
        blank_message="Document revisions cannot be blank",
        required_message="Document revisions is required"
    )
    date_requested = serializers.DateField(
        error_messages={"invalid": "Date requested must use this format: YYYY-MM-DD"}
    )
    date_needed = serializers.DateField(
        error_messages={"invalid": "Date needed must use this format: YYYY-MM-DD"}
    )
    project_name = CustomCharField(
        blank_message="Project name cannot be blank",
        required_message="Project name is required"
    )
    location = CustomCharField(
        blank_message="Location cannot be blank",
        required_message="Location is required"
    )
    prepared_by = CustomCharField(
        blank_message="Prepared by cannot be blank",
        required_message="Prepared by is required"
    )
    remarks = CustomCharField(
        blank_message="Remarks cannot be blank",
        required_message="Remarks is required"
    )
    approved_by = CustomCharField(
        blank_message="Approved by cannot be blank",
        required_message="Approved by is required"
    )
    request_status = CustomCharField(
        blank_message="Request status cannot be blank",
        required_message="Request status is required"
    )
    final_remarks = CustomCharField(
        blank_message="Remarks cannot be blank",
        required_message="Remarks is required"
    )
    requested_signature = Base64ImageField()
    approved_signature = Base64ImageField()
    date_time = serializers.DateTimeField(
        format='%m/%d/%Y', input_formats=['%m/%d/%Y'],
        error_messages={"invalid": "Date time must use this format: MM/DD/YYYY"}
    )
    purchase_items = UpdatePurchaseItemsSerializer(many=True)

    class Meta:
        model = PurchaseRequest
        fields = [
            'id', 'pr_no', 'document_revisions',
            'date_requested', 'date_needed', 'project_name',
            'location', 'prepared_by', 'requested_signature', 'remarks',
            'approved_by', 'approved_signature', 'date_time', 'request_status',
            'final_remarks', 'purchase_items'
        ]

    
    def to_internal_value(self, data):

        if data.get('date_requested') in (None, "") or data.get('date_requested').strip() == "":
            raise_validation("Date requested cannot be blank")
        if data.get('date_needed') in (None, "") or data.get('date_needed').strip() == "":
            raise_validation("Date needed cannot be blank")
        if data.get('date_time') in (None, "") or data.get('date_time').strip() == "":
            raise_validation("Date time cannot be blank")
            
        return super().to_internal_value(data)

    def validate(self, attrs):

        if is_field_empty(attrs["document_revisions"]):
            raise_validation("Document revisions cannot be blank")

        allowed_status = RequestStatus.AVAILABLE_CHOICES

        if is_field_empty(attrs["project_name"]):
            raise_validation("Project name cannot be blank")

        if is_field_empty(attrs["location"]):
            raise_validation("Location cannot be blank")

        if is_field_empty(attrs["prepared_by"]):
            raise_validation("Prepared by cannot be blank")

        if is_field_empty(attrs["remarks"]):
            raise_validation("Remarks cannot be blank")

        if is_field_empty(attrs["approved_by"]):
            raise_validation("Approved by cannot be blank")

        if is_field_empty(attrs["request_status"]):
            raise_validation("Request status cannot be blank")

        if attrs["request_status"] not in allowed_status:
            raise_validation("Invalid request status")

        if is_field_empty(attrs["final_remarks"]):
            raise_validation("Remarks cannot be blank")


        return attrs
    
    def update(self, instance, validated_data): 

        # Extract the nested data items
        items_data = validated_data.pop('purchase_items')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()


        # Convert keys to string for comparison
        existing_items = {str(item.id): item for item in instance.purchase_items.all()}
        # Update existing delivery items
        for item_data in items_data:
            item_id = str(item_data.get("purchase_item_id"))

            if item_id and item_id in existing_items:
                item_instance = existing_items[item_id]

                for attr, value in item_data.items():
                    setattr(item_instance, attr, value)

                item_instance.save()

        return instance


