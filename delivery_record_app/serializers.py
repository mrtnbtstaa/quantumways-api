from rest_framework import serializers
from .models import DeliveryRecord, DeliveryItem
from quantumways.utils import is_field_empty, raise_validation, CustomCharField, decode_base64_image_from_csv
from quantumways.utils import Base64ImageField
from quantumways.services.services import create_bulk_items
from collections import defaultdict
from datetime import datetime
from io import BytesIO
from openpyxl import load_workbook
from master_list_app.models import Product

class AddDeliveryItemSerializer(serializers.ModelSerializer):

    item_no = serializers.IntegerField(
        error_messages={
            "null": "Item no cannot have null value",
            "invalid": "Invalid item no value"
        }
    )
    quantity = serializers.IntegerField(
        error_messages={
            "null": "Quantity cannot have null value",
            "invalid": "Invalid quantity value"
        }
    )
    unit = CustomCharField(
        blank_message="Unit cannot be blank",
        required_message="Unit is required",
        error_messages={
            "null": "Unit cannot be null"
        }
    )
    item_description = CustomCharField(
        blank_message="Item Description cannot be blank",
        required_message="Item Description is required",
        error_messages={
            "null": "Item description cannot be null"
        }
    )


    class Meta:
        model = DeliveryItem
        fields = ['item_no', 'quantity', 'unit', 'item_description']


    def validate(self, attrs):

        if attrs["item_no"] < 0:
            raise_validation("Item no must be positive value")

        if attrs["quantity"] < 0:
            raise_validation("Quantity must be positive value")

        if is_field_empty(attrs["unit"]):
            raise_validation("Unit cannot be blank")

        if is_field_empty(attrs["item_description"]):
            raise_validation("Item description cannot be blank")

        if not Product.objects.filter(item__icontains=attrs["item_description"]).exists():
            raise_validation("No item description found")


        return attrs


class ImportXlsxInDeliveryRecordSerializer(serializers.Serializer):

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

    
        grouped_data = defaultdict(list)
        failed_imports = []
        created_delivery_records = []

        headers = [cell.value for cell in sheet[1]]

        # Group rows
        for rows in sheet.iter_rows(min_row=2, values_only=True):
            row_dict = dict(zip(headers, rows))
            dr_no = row_dict.get('DR No')
            if dr_no:
                grouped_data[dr_no].append(row_dict)


        # Process each group

        for dr_no, rows in grouped_data.items():
            try:

                first = rows[0]

                dr_no = (
                    f"000{first.get('DR No', None)}"
                    if not str(first.get('DR No', None)).startswith('0')
                    else first.get('DR No', None)
                )

                if not DeliveryRecord.objects.filter(dr_no=dr_no).exists():

                    dr_data = {
                        "dr_no": dr_no,
                        "document_revisions": first["Document Revisions"],
                        "date": datetime.strptime(first["Date"], '%m/%d/%Y').date(),
                        "origin_from": first['Origin From'],
                        "delivered_by": first['Delivered By'],
                        "delivered_to": first['Delivered To'],
                        "received_by": first.get('Received By', None),
                        "approved_by": decode_base64_image_from_csv(first.get('Approved By', None)),
                        "remarks": first['Remarks']
                    }

                    items_data = [
                        {
                            "item_no": row["Item No"],
                            "quantity": row['Quantity'],
                            "unit": row['Unit'],
                            "item_description": row['Item Description'],
                        }
                        for row in rows
                    ]

                    delivery_records = create_bulk_items(
                        main_model=DeliveryRecord,
                        child_model=DeliveryItem,
                        main_data=dr_data,
                        children_data=items_data,
                        foreign_key_name='delivery_record'
                    )

                    created_delivery_records.append(delivery_records)

                else:
                    continue

            except Exception as e:
                failed_imports.append({
                    "dr_no": dr_no,
                    "error": str(e)
                })

        if failed_imports:
            raise serializers.ValidationError({
                "message": "Some rows failed to import.",
                "failures": failed_imports
            })
        
        return created_delivery_records


class AddDeliveryRecordSerializer(serializers.ModelSerializer):

    document_revisions = CustomCharField(
        blank_message="Document revisions cannot be blank",
        required_message="Document revisions is required",
        error_messages={
            "null": "Document revisions cannot be null"
        }
    )
    date = serializers.DateField(
        allow_null=False,
        input_formats=['%m/%d/%Y'],
        error_messages={
            "invalid": "Date must use this format: MM/DD/YYYY",
            "null": "Date cannot be null"
        }
    )
    origin_from = CustomCharField(
        blank_message="Origin from cannot be blank",
        required_message="Origin from is required",
        error_messages={
            "null": "Origin from cannot be null"
        }
    )
    delivered_by = CustomCharField(
        blank_message="Delivered by cannot be blank",
        required_message="Delivered by is required",
        error_messages={
            "null": "Delivered by cannot be null"
        }
    )
    delivered_to = CustomCharField(
        blank_message="Delivered to cannot be blank",
        required_message="Delivered to is required",
        error_messages={
            "null": "Delivered to cannot be null"
        }
    )
    received_by = CustomCharField(
        None,
        None,
        required=False,
        allow_null=True,
        allow_blank=True
    )
    approved_by = Base64ImageField(allow_null=True)
    remarks = CustomCharField(
        blank_message="Remarks cannot be blank",
        required_message="Remarks is required",
        error_messages={
            "null": "Remarks cannot be null"
        }
    )
    items = AddDeliveryItemSerializer(many=True)

    class Meta:
        model = DeliveryRecord
        fields = '__all__'

    def to_internal_value(self, data):
        
        if data["date"] in (None, "") or data["date"].strip() == "":
            raise_validation("Date cannot be blank")

        return super().to_internal_value(data)

    def validate(self, attrs):

        if DeliveryRecord.objects.filter(dr_no=attrs["dr_no"]).exists():
            raise_validation(f"DR No: {attrs["dr_no"]} already exists")

        if is_field_empty(attrs["document_revisions"]):
            raise_validation("Document revisions cannot be blank")

        if is_field_empty(attrs["origin_from"]):
            raise_validation("Origin from cannot be blank")

        if is_field_empty(attrs["delivered_by"]):
            raise_validation("Delivered by cannot be blank")

        if is_field_empty(attrs["delivered_to"]):
            raise_validation("Delivered to cannot be blank")

        if is_field_empty(attrs["remarks"]):
            raise_validation("Remarks cannot be blank")
        
        return attrs
        

    def create(self, validated_data):
        
        items_data = validated_data.pop('items')

        delivery_records = create_bulk_items(
            main_model=DeliveryRecord,
            child_model=DeliveryItem,
            main_data=validated_data,
            children_data=items_data,
            foreign_key_name='delivery_record'
        )

        # items = delivery_records.items.all().order_by('id')

        # last_no = DeliveryItem.objects.aggregate(max_no=Max('item_no'))['max_no'] or 0

        # for item in items:
        #     last_no += 1
        #     item.item_no = last_no
        #     item.save(update_fields=['item_no'])

        return delivery_records

class ViewListDeliveryRecordsSerializer(serializers.ModelSerializer):

    delivery_record_id = serializers.UUIDField(source='id')

    class Meta:
        model = DeliveryRecord
        fields = ['delivery_record_id', 'dr_no', 'date']


class SearchListDeliveryRecordsSerializer(serializers.ModelSerializer):

    delivery_record_id = serializers.UUIDField(source='id')

    class Meta:
        model = DeliveryRecord
        fields = ['delivery_record_id', 'dr_no', 'date']

class ViewDeliveryItemDetailsSerializer(serializers.ModelSerializer):

    delivery_item_id = serializers.UUIDField(source='id')

    class Meta:
        model = DeliveryItem
        fields = [
            'delivery_item_id', 'item_no', 'quantity', 'unit', 'item_description'
        ]


class ViewDeliveryRecordDetailsSerializer(serializers.ModelSerializer):

    delivery_record_id = serializers.UUIDField(source='id')
    items = ViewDeliveryItemDetailsSerializer(many=True)
    date = serializers.DateField(format='%m/%d/%Y')

    class Meta:
        model = DeliveryRecord
        fields = [
            'delivery_record_id', 'dr_no', 'document_revisions', 'date',
            'origin_from', 'delivered_by', 'delivered_to',
            'received_by', 'approved_by', 'remarks', 'items'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)

        dr_no = data.pop('dr_no')

        data["dr_no"] = (
            f"0{dr_no}"
            if not dr_no.startswith('0')
            else dr_no
        )

        data["items"] = data.pop('items')

        return data



class UpdateDeliveryItemSerializer(serializers.ModelSerializer):

    delivery_item_id = CustomCharField(
        blank_message="Delivery Item ID cannot be blank",
        required_message="Delivery Item ID is required for updating",
    )
    item_no = serializers.IntegerField(
        error_messages={
            "null": "Item no cannot have null value",
            "invalid": "Invalid item no value"
        }
    )
    quantity = serializers.IntegerField(
        error_messages={
            "null": "Quantity cannot have null value",
            "invalid": "Invalid quantity value"
        }
    )
    unit = CustomCharField(
        blank_message="Unit cannot be blank",
        required_message="Unit is required",
        error_messages={
            "null": "Unit cannot be null"
        }
    )
    item_description = CustomCharField(
        blank_message="Item description cannot be blank",
        required_message="Item description is required",
        error_messages={
            "null": "Item description cannot be null"
        }
    )

    class Meta:
        model = DeliveryItem
        fields = ['delivery_item_id', 'item_no', 'quantity', 'unit', 'item_description']

    def validate(self, attrs):

        if is_field_empty(attrs["delivery_item_id"]):
            raise_validation("Delivery Item ID is required for updating")

        if attrs["item_no"] < 0:
            raise_validation("Item no must be positive value")

        if attrs["quantity"] < 0:
            raise_validation("Quantity must be positive value")

        if is_field_empty(attrs["unit"]):
            raise_validation("Unit cannot be blank")

        if is_field_empty(attrs["item_description"]):
            raise_validation("Item description cannot be blank")

        if not Product.objects.filter(item__icontains=attrs["item_description"]).exists():
            raise_validation("No item description found")

        return attrs

class UpdateDeliveryRecordSerializer(serializers.ModelSerializer):

    document_revisions = CustomCharField(
        blank_message="Document revisions cannot be blank",
        required_message="Document revisions is required",
        error_messages={
            "null": "Document revisions cannot be null"
        }
    )
    date = serializers.DateField(
        allow_null=False,
        input_formats=['%m/%d/%Y'],
        error_messages={
            "invalid": "Date must use this format: MM/DD/YYYY",
            "null": "Date cannot be null"
        }
    )
    origin_from = CustomCharField(
        blank_message="Origin from cannot be blank",
        required_message="Origin from is required",
        error_messages={
            "null": "Origin from cannot be null"
        }
    )
    delivered_by = CustomCharField(
        blank_message="Delivered by cannot be blank",
        required_message="Delivered by is required",
        error_messages={
            "null": "Delivered by cannot be null"
        }
    )
    delivered_to = CustomCharField(
        blank_message="Delivered to cannot be blank",
        required_message="Delivered to is required",
        error_messages={
            "null": "Delivered to cannot be null"
        }
    )
    received_by = CustomCharField(
        None,
        None,
        required=False,
        allow_null=True,
        allow_blank=True
    )
    approved_by = Base64ImageField(allow_null=True)
    remarks = CustomCharField(
        blank_message="Remarks cannot be blank",
        required_message="Remarks is required",
        error_messages={
            "null": "Remarks cannot be null"
        }
    )
    items = AddDeliveryItemSerializer(many=True)

    class Meta:
        model = DeliveryRecord
        fields = [
            'dr_no', 'document_revisions', 'date',
            'origin_from', 'delivered_by', 'delivered_to',
            'received_by', 'approved_by', 'remarks', 'items'
        ]

    
    def to_internal_value(self, data):

        if data["date"] in (None, "") or data["date"].strip() == "":
            raise_validation("Date cannot be blank")

        return super().to_internal_value(data)

    def validate(self, attrs):

        if is_field_empty(attrs["document_revisions"]):
            raise_validation("Document revisions cannot be blank")

        if is_field_empty(attrs["origin_from"]):
            raise_validation("Origin from cannot be blank")

        if is_field_empty(attrs["delivered_by"]):
            raise_validation("Delivered by cannot be blank")

        if is_field_empty(attrs["delivered_to"]):
            raise_validation("Delivered to cannot be blank")

        if is_field_empty(attrs["remarks"]):
            raise_validation("Remarks cannot be blank")
        
        return attrs
    
    def update(self, instance, validated_data): 

        # Extract the nested data items
        items_data = validated_data.pop('items')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()


        # Convert keys to string for comparison
        existing_items = {str(item.id): item for item in instance.items.all()}
        # Update existing delivery items
        for item_data in items_data:
            print(item_data)
            item_id = str(item_data.get("delivery_item_id"))

            if item_id and item_id in existing_items:
                item_instance = existing_items[item_id]

                for attr, value in item_data.items():
                    setattr(item_instance, attr, value)

                item_instance.save()

        return instance