from rest_framework import serializers
from .models import PettyCash, PettyItem
from quantumways.utils import is_field_empty, raise_validation, CustomCharField
from quantumways.services.services import create_bulk_items
from collections import defaultdict
from django.db import transaction
from openpyxl import load_workbook
from io import BytesIO
from django.db.models import Sum
from datetime import datetime
from master_list_app.models import Product

class AddPettyItemsInTopManagementSerializer(serializers.ModelSerializer):

    no_of_items = serializers.IntegerField(
        error_messages={
            "blank": "Quantity cannot be blank",
            "null": "No of items cannot have null value",
            "invalid": "Invalid no of items value"
        }
    )
    unit = CustomCharField(
        blank_message="Unit cannot be blank",
        required_message="Unit is required"
    )
    services_purchased = CustomCharField(
        blank_message="Services purchased cannot be blank",
        required_message="Services purchased is required",
    )
    unit_cost = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        error_messages={
            "blank": "Unit cost cannot be blank",
            "null": "Unit cost cannot have null value",
            "invalid": "Invalid unit cost value"
        }
    )
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        error_messages={
            "blank": "Amount cannot be blank",
            "null": "Amount cannot have null value",
            "invalid": "Invalid amount value"
        }
    )
    

    class Meta:
        model = PettyItem
        fields = ['no_of_items', 'unit', 'services_purchased', 'unit_cost', 'amount']


    def validate(self, attrs):

        no_of_items = attrs["no_of_items"]
        unit_cost = attrs["unit_cost"]
        amount = attrs["amount"]

        if no_of_items < 0:
            raise_validation("No of items must be positive value")
            
        if is_field_empty(attrs["unit"]):
            raise_validation("Unit cannot be blank")

        if is_field_empty(attrs["services_purchased"]):
            raise_validation("Services purchased cannot be blank")

        if not Product.objects.filter(item__icontains=attrs["services_purchased"]).exists():
            raise_validation("No services purchased found")

        if unit_cost < 0:
            raise_validation("Unit cost must be positive value")

        if amount < 0:
            raise_validation("Amount must be positive value")


        return attrs
    

class AddPettyCashInTopManagementSerializer(serializers.ModelSerializer):

    control_no = CustomCharField(
        None,
        None,
        required=False,
        allow_blank=True
    )
    document_revisions = CustomCharField(
        blank_message="Document revisions cannot be blank",
        required_message="Document revisions is required"
    )
    pc_given = serializers.IntegerField(
        error_messages={
            "blank": "Pc given cannot be blank",
            "null": "Pc givenn cannot have null value",
            "invalid": "Invalid pc given value"
        }
    )
    date = serializers.DateField(
        format='%m/%d/%Y',
        input_formats=['%m/%d/%Y'],
        error_messages={
            "null": "Date cannot be blank",
            "invalid": "Date must use this format: MM/DD/YYYY"
        }
    )
    requested_and_received_by = CustomCharField(
        blank_message="Requested and received by cannot be blank",
        required_message="Requested and received by is required"
    )
    location = CustomCharField(
        blank_message="Location cannot be blank",
        required_message="Location is required"
    )
    released_by = CustomCharField(
        blank_message="Released by cannot be blank",
        required_message="Released by is required"
    )
    remarks = CustomCharField(
        blank_message="Remarks cannot be blank",
        required_message="Remarks is required"
    )

    items = AddPettyItemsInTopManagementSerializer(many=True)
    
    
    class Meta:
        model = PettyCash
        fields = ['control_no', 'document_revisions', 'pc_given', 'date', 'requested_and_received_by', 'location', 'released_by', 'remarks', 'items']

    def to_internal_value(self, data):
        if data["date"] in (None, "") or data["date"].strip() == "":
            raise_validation("Date cannot be blank")
        return super().to_internal_value(data)

    def validate(self, attrs):

        if PettyCash.objects.filter(control_no=attrs["control_no"]).exists():
            raise_validation(f"Control No: {attrs["control_no"]} already exists")

        if is_field_empty(attrs["document_revisions"]):
            raise_validation("Document revisions cannot be blank")

        if attrs["pc_given"] < 0:
            raise_validation("Pc given must be positive value")

        if is_field_empty(attrs["requested_and_received_by"]):
            raise_validation("Requested and received by cannot be blank")

        if is_field_empty(attrs["location"]):
            raise_validation("Location cannot be blank")

        if is_field_empty(attrs["released_by"]):
            raise_validation("Released by cannot be blank")

        if is_field_empty(attrs["remarks"]):
            raise_validation("Remarks cannot be blank")

        return attrs
    
    def create(self, validated_data):
        
        # Extract the nested serializers data
        items_data = validated_data.pop('items')
        with transaction.atomic():

            try:
            
                # Create the purchase order associated with the purchase items
                petty_cash = create_bulk_items(
                    main_model=PettyCash,
                    child_model=PettyItem,
                    main_data=validated_data,
                    children_data=items_data,
                    foreign_key_name='petty_cash'
                )

                total = petty_cash.items.aggregate(total=Sum('amount'))['total'] or 0
                petty_cash.total = total
                petty_cash.save(update_fields=['total'])

                return petty_cash

            except Exception as e:
                raise_validation(f"Something went wrong when creating the data {e}")

class ImportXlsxInPettyCashSerializer(serializers.Serializer):

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
        created_petty_data = []

        headers = [cell.value for cell in sheet[1]]

        # Group rows
        for rows in sheet.iter_rows(min_row=2, values_only=True):
            row_dict = dict(zip(headers, rows))
            control_no = row_dict.get('Control No')
            if control_no:
                grouped_data[control_no].append(row_dict)


        # Process each group
        for pc_control_no, rows in grouped_data.items():
            try:

                first = rows[0]

                control_no = (
                    f"0000{str(first["Control No"])}"
                    if not str(first["Control No"]).startswith("0")
                    else str(first["Control No"])
                )

                if not PettyCash.objects.filter(control_no=control_no).exists():
                    

                    pc_data = {
                        "control_no": control_no,
                        "document_revisions": first["Document Revisions"],
                        "date": datetime.strptime(first["Date"], '%m/%d/%Y').date(),
                        "pc_given": str(first["PC Given"]),
                        "requested_and_received_by": first["Requested and Received by"],
                        "location": first["Location"],
                        "released_by": first["Released by"],
                        "remarks": first["Remarks"],
                    }

                    items_data = [
                        {
                            "no_of_items": row['No of Items'],
                            "unit": row['Unit'],
                            "services_purchased": row['Description of Items/Services Purchased'],
                            "unit_cost": row['Unit Cost'],
                            "amount": row['Amount']
                        }
                        for row in rows
                    ]

                    petty_cash = create_bulk_items(
                        main_model=PettyCash,
                        child_model=PettyItem,
                        main_data=pc_data,
                        children_data=items_data,
                        foreign_key_name='petty_cash'
                    )

                    total = petty_cash.items.aggregate(total=Sum('amount'))['total'] or 0
                    petty_cash.total = total
                    petty_cash.save(update_fields=['total'])

                    
                    created_petty_data.append(petty_cash)
                else:
                    continue

            except Exception as e:
                failed_imports.append({
                    "control_no": pc_control_no,
                    "error": str(e)
                })

        if failed_imports:
            raise serializers.ValidationError({
                "message": "Some rows failed to import.",
                "failures": failed_imports
            })
        
        return created_petty_data




class ViewPettyCashSerializer(serializers.ModelSerializer):
    petty_cash_id = serializers.UUIDField(source='id')
    date = serializers.DateField(format='%m/%d/%Y')

    class Meta:
        model = PettyCash
        fields = ['petty_cash_id', 'control_no', 'date']


class SearchPettyCashSerializer(serializers.ModelSerializer):
    petty_cash_id = serializers.UUIDField(source='id')
    date = serializers.DateField(format='%m/%d/%Y')

    class Meta:
        model = PettyCash
        fields = ['petty_cash_id', 'control_no', 'date']

class ViewPettyItemsDetailsSerializer(serializers.ModelSerializer):

    petty_item_id = serializers.UUIDField(source='id')

    class Meta:
        model = PettyItem
        fields = ['petty_item_id', 'no_of_items', 'unit', 'services_purchased', 'unit_cost', 'amount']

class ViewPettyCashDetailsSerializer(serializers.ModelSerializer):
    
    petty_cash_id = serializers.UUIDField(source='id')
    items = ViewPettyItemsDetailsSerializer(many=True)
    date = serializers.DateField(format='%m/%d/%Y')
    class Meta:
        model = PettyCash
        fields = [
            'petty_cash_id', 'control_no' ,'document_revisions', 'pc_given', 'date',
            'total', 'requested_and_received_by', 'location',
            'released_by', 'remarks', 'items'
        ]


class UpdatePettyItemsSerializer(serializers.ModelSerializer):

    petty_item_id = CustomCharField(
        blank_message="Id must be present to update the petty items",
        required_message="Petty Item ID is required",
    )

    no_of_items = serializers.IntegerField(
        error_messages={
            "blank": "Quantity cannot be blank",
            "null": "No of items cannot have null value",
            "invalid": "Invalid no of items value"
        }
    )
    unit = CustomCharField(
        blank_message="Unit cannot be blank",
        required_message="Unit is required"
    )
    services_purchased = CustomCharField(
        blank_message="Services purchased cannot be blank",
        required_message="Services purchased is required",
    )
    unit_cost = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        error_messages={
            "blank": "Unit cost cannot be blank",
            "null": "Unit cost cannot have null value",
            "invalid": "Invalid unit cost value"
        }
    )
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        error_messages={
            "blank": "Amount cannot be blank",
            "null": "Amount cannot have null value",
            "invalid": "Invalid amount value"
        }
    )

    class Meta:
        model = PettyItem
        fields = ['petty_item_id', 'no_of_items', 'unit', 'services_purchased', 'unit_cost', 'amount']

    def validate(self, attrs):

        no_of_items = attrs["no_of_items"]
        unit_cost = attrs["unit_cost"]
        amount = attrs["amount"]

        if is_field_empty(attrs["petty_item_id"]):
            raise_validation("Petty Item ID is required for updating")

        if no_of_items < 0:
            raise_validation("No of items must be positive value")
            
        if is_field_empty(attrs["unit"]):
            raise_validation("Unit cannot be blank")

        if is_field_empty(attrs["services_purchased"]):
            raise_validation("Services purchased cannot be blank")

        if not Product.objects.filter(item__icontains=attrs["services_purchased"]).exists():
            raise_validation("No services purchased found")

        if unit_cost < 0:
            raise_validation("Unit cost must be positive value")

        if amount < 0:
            raise_validation("Amount must be positive value")

        return attrs

class UpdatePettyCashSerializer(serializers.ModelSerializer):

    control_no = CustomCharField(
        None,
        None,
        required=False,
        allow_blank=True
    )
    document_revisions = CustomCharField(
        blank_message="Document revisions cannot be blank",
        required_message="Document revisions is required"
    )
    pc_given = serializers.IntegerField(
        error_messages={
            "blank": "Pc given cannot be blank",
            "null": "Pc given cannot have null value",
            "invalid": "Invalid pc given value"
        }
    )
    date = serializers.DateField(
        format='%m/%d/%Y',
        input_formats=['%m/%d/%Y'],
        error_messages={
            "null": "Date cannot be blank",
            "invalid": "Date must use this format: MM/DD/YYYY"
        }
    )
    requested_and_received_by = CustomCharField(
        blank_message="Requested and received by cannot be blank",
        required_message="Requested and received by is required"
    )
    location = CustomCharField(
        blank_message="Location cannot be blank",
        required_message="Location is required"
    )
    released_by = CustomCharField(
        blank_message="Released by cannot be blank",
        required_message="Released by is required"
    )
    remarks = CustomCharField(
        blank_message="Remarks cannot be blank",
        required_message="Remarks is required"
    )
    items = UpdatePettyItemsSerializer(many=True)

    class Meta:
        model = PettyCash
        fields = [
            'control_no', 'document_revisions',
            'pc_given', 'date', 'requested_and_received_by',
            'location', 'released_by', 'remarks', 'items'
        ]

    
    def to_internal_value(self, data):

        if data["date"] in (None, "") or data["date"].strip() == "":
            raise_validation("Date cannot be blank")
        return super().to_internal_value(data)

    def validate(self, attrs):

        if is_field_empty(attrs["document_revisions"]):
            raise_validation("Document revisions cannot be blank")

        if attrs["pc_given"] < 0:
            raise_validation("Pc given must be positive value")

        if is_field_empty(attrs["requested_and_received_by"]):
            raise_validation("Requested and received by cannot be blank")

        if is_field_empty(attrs["location"]):
            raise_validation("Location cannot be blank")

        if is_field_empty(attrs["released_by"]):
            raise_validation("Released by cannot be blank")

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
            item_id = str(item_data.get("petty_item_id"))
            print("Item ID from payload:", item_id)

            if item_id and item_id in existing_items:
                item_instance = existing_items[item_id]

                for attr, value in item_data.items():
                    setattr(item_instance, attr, value)

                item_instance.save()

        total = instance.items.aggregate(total=Sum('amount'))['total'] or 0
        instance.total = total
        instance.save(update_fields=['total'])

        return instance
