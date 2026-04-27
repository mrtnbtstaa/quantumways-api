from rest_framework import serializers
from .models import Record, RecordItem
from quantumways.utils import raise_validation, CustomCharField
from quantumways.services.services import create_bulk_items
from django.db.models import Sum
from decimal import Decimal, InvalidOperation
from django.db import transaction

class AddRecordItemsSerializer(serializers.ModelSerializer):
    
    pr_no = serializers.IntegerField(
        error_messages={
            "blank": "Pr no cannot be blank",
            "null": "Pr no cannot have null value",
            "invalid": "Invalid pr no value"
        }
    )
    pcv_no = serializers.IntegerField(
        error_messages={
            "blank": "Pcv no cannot be blank",
            "null": "Pcv no cannot have null value",
            "invalid": "Invalid pcv no value"
        }
    )
    dr_no = serializers.IntegerField(
        error_messages={
            "blank": "Dr no cannot be blank",
            "null": "Dr no cannot have null value",
            "invalid": "Invalid dr no value"
        }
    )
    vl = serializers.IntegerField(
        error_messages={
            "blank": "Vl no cannot be blank",
            "null": "Vl no cannot have null value",
            "invalid": "Invalid vl no value"
        }
    )
    po_no = serializers.IntegerField(
        error_messages={
            "blank": "Po no cannot be blank",
            "null": "Po no cannot have null value",
            "invalid": "Invalid Po no value"
        }
    )
    project_site = CustomCharField(
        blank_message="Project site cannot be blank",
        required_message="Project site is required"
    )
    person_in_charge = CustomCharField(
        blank_message="Person in charge cannot be blank",
        required_message="Person in charge is required"
    )
    equipment = CustomCharField(
        blank_message="Equipment cannot be blank",
        required_message="Equipment is required"
    )
    supplier = CustomCharField(
        blank_message="Supplier cannot be blank",
        required_message="Supplier is required"
    )
    type_of_receipt = CustomCharField(
        blank_message="Type of receipt cannot be blank",
        required_message="Type of receipt is required"
    )
    invoice_receipt_no = CustomCharField(
        blank_message="Invoice receipt no cannot be blank",
        required_message="Invoice receipt no is required"
    )
    receipt_issued_to = CustomCharField(
        blank_message="Receipt issued to cannot be blank",
        required_message="Receipt issued to is required"
    )
    qty = serializers.FloatField(
        error_messages={
            "blank": "Quantity cannot be blank",
            "null": "Quantity cannot have null value",
            "invalid": "Invalid quantity value"
        }
    )
    unit = CustomCharField(
        blank_message="Unit cannot be blank",
        required_message="Unit is required"
    )
    product_name = CustomCharField(
        blank_message="Product name cannot be blank",
        required_message="Product name is required"
    )
    item_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        error_messages={
            "blank": "Item price cannot be blank",
            "null": "Item price cannot have null value",
            "invalid": "Invalid item price value"
        }
    )
    item_unit = CustomCharField(
        blank_message="Item unit cannot be blank",
        required_message="Item unit is required"
    )

    class Meta:
        model = RecordItem
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'id', 'record', 'total_amount', 'supplier_receipt_amount']


    def validate(self, attrs):
        
        if attrs["pr_no"] < 0:
            raise_validation("Pr no must be a positive value")
        if attrs["pcv_no"] < 0:
            raise_validation("Pcv no must be a positive value")
        if attrs["dr_no"] < 0:
            raise_validation("Dr no must be a positive value")
        if attrs["vl"] < 0:
            raise_validation("Vl no must be a positive value")
        if attrs["po_no"] < 0:
            raise_validation("Po no must be a positive value")

        return attrs

class AddRecordSerializer(serializers.ModelSerializer):

    date = serializers.DateField(input_formats=['%m/%d/%Y'], error_messages={
        "invalid": "Date must use this format: MM/DD/YYYY"
    })
    petty_cash_given = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        error_messages={
            "blank": "Petty cash given cannot be blank",
            "null": "Petty cash given cannot have null value",
            "invalid": "Invalid petty cash given value"
        }
    )

    items = AddRecordItemsSerializer(many=True)

    class Meta:
        model = Record
        fields = ['date', 'petty_cash_given', 'items']

    
    def validate_petty_cash_given(self, value):

        if value < 0:
            raise_validation("Petty cash given must be a positive value")

        return value


    def create(self, validated_data):
        
        try:

            with transaction.atomic():

                items_data = validated_data.pop('items')
                
                for item in items_data:
                    try:

                        qty = Decimal(str(item.get("qty", 0)))
                        item_price = Decimal(str(item.get("item_price", 0)))
                        total_amount = item["total_amount"] = qty * item_price
                        item["supplier_receipt_amount"] = total_amount

                    except (InvalidOperation, TypeError):
                        item["total_amount"] = None
                        item["supplier_receipt_amount"] = None

                records = create_bulk_items(
                    main_model=Record,
                    child_model=RecordItem,
                    main_data=validated_data,
                    children_data=items_data,
                    foreign_key_name='record'
                )

                total_amount_per_person = records.items.aggregate(total=Sum('supplier_receipt_amount'))['total'] or 0
                records.amount_site_per_person = total_amount_per_person


                remaining_amount_refunded = abs(total_amount_per_person - validated_data.get('petty_cash_given'))
                records.amount_refunded = remaining_amount_refunded
     
                records.save(update_fields=['amount_site_per_person', 'amount_refunded'])


                return records
            
        except Exception as e:
            raise_validation(e)

class ViewRecordItemSerializer(serializers.ModelSerializer):

    record_item_id = serializers.UUIDField(source='id')

    class Meta: 
        model = RecordItem
        fields = ['record_item_id', 'pr_no', 'pcv_no', 'dr_no', 'vl', 'po_no', 'project_site', 'supplier', 'type_of_receipt']


class ViewRecordSerializer(serializers.ModelSerializer):
    date = serializers.DateField(format='%m/%d/%Y')
    items = ViewRecordItemSerializer(many=True)
    record_id = serializers.UUIDField(source='id')

    class Meta:
        model = Record
        fields = ['record_id', 'date', 'items']


class SearchRecordSerializer(serializers.ModelSerializer):
    date = serializers.DateField(format='%m/%d/%Y')
    items = ViewRecordItemSerializer(many=True)
    record_id = serializers.UUIDField(source='id')

    class Meta:
        model = Record
        fields = ['record_id', 'date', 'items']


class ViewRecordItemDetailsSerializer(serializers.ModelSerializer):

    record_item_id = serializers.UUIDField(source='id')

    class Meta:
        model = RecordItem
        fields = [
            'record_item_id', 'pr_no', 'pcv_no',
            'dr_no', 'vl', 'po_no', 'project_site',
            'person_in_charge', 'equipment', 'supplier',
            'type_of_receipt', 'invoice_receipt_no', 'receipt_issued_to',
            'qty', 'unit', 'product_name', 'item_price', 'item_unit',
            'total_amount', 'supplier_receipt_amount'
        ]


class ViewRecordDetailsSerializer(serializers.ModelSerializer):

    record_id = serializers.UUIDField(source='id')
    date = serializers.DateField(format='%m/%d/%Y')
    items = ViewRecordItemDetailsSerializer(many=True)
    class Meta:
        model = Record
        fields = ['record_id', 'date', 'amount_site_per_person', 'petty_cash_given', 'amount_refunded', 'items']




class UpdateRecordItemsSerializer(serializers.ModelSerializer):

    record_item_id = serializers.CharField()
    
    pr_no = serializers.IntegerField(
        error_messages={
            "blank": "Pr no cannot be blank",
            "null": "Pr no cannot have null value",
            "invalid": "Invalid pr no value"
        }
    )
    pcv_no = serializers.IntegerField(
        error_messages={
            "blank": "Pcv no cannot be blank",
            "null": "Pcv no cannot have null value",
            "invalid": "Invalid pcv no value"
        }
    )
    dr_no = serializers.IntegerField(
        error_messages={
            "blank": "Dr no cannot be blank",
            "null": "Dr no cannot have null value",
            "invalid": "Invalid dr no value"
        }
    )
    vl = serializers.IntegerField(
        error_messages={
            "blank": "Vl no cannot be blank",
            "null": "Vl no cannot have null value",
            "invalid": "Invalid vl no value"
        }
    )
    po_no = serializers.IntegerField(
        error_messages={
            "blank": "Po no cannot be blank",
            "null": "Po no cannot have null value",
            "invalid": "Invalid Po no value"
        }
    )
    project_site = CustomCharField(
        blank_message="Project site cannot be blank",
        required_message="Project site is required"
    )
    person_in_charge = CustomCharField(
        blank_message="Person in charge cannot be blank",
        required_message="Person in charge is required"
    )
    equipment = CustomCharField(
        blank_message="Equipment cannot be blank",
        required_message="Equipment is required"
    )
    supplier = CustomCharField(
        blank_message="Supplier cannot be blank",
        required_message="Supplier is required"
    )
    type_of_receipt = CustomCharField(
        blank_message="Type of receipt cannot be blank",
        required_message="Type of receipt is required"
    )
    invoice_receipt_no = CustomCharField(
        blank_message="Invoice receipt no cannot be blank",
        required_message="Invoice receipt no is required"
    )
    receipt_issued_to = CustomCharField(
        blank_message="Receipt issued to cannot be blank",
        required_message="Receipt issued to is required"
    )
    qty = serializers.FloatField(
        error_messages={
            "blank": "Quantity cannot be blank",
            "null": "Quantity cannot have null value",
            "invalid": "Invalid quantity value"
        }
    )
    unit = CustomCharField(
        blank_message="Unit cannot be blank",
        required_message="Unit is required"
    )
    product_name = CustomCharField(
        blank_message="Product name cannot be blank",
        required_message="Product name is required"
    )
    item_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        error_messages={
            "blank": "Item price cannot be blank",
            "null": "Item price cannot have null value",
            "invalid": "Invalid item price value"
        }
    )
    item_unit = CustomCharField(
        blank_message="Item unit cannot be blank",
        required_message="Item unit is required"
    )
    supplier_receipt_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        error_messages={
            "blank": "Supplier receipt amount cannot be blank",
            "null": "Supplier receipt amount cannot have null value",
            "invalid": "Invalid supplier receipt amount value"
        }
    )

    class Meta:
        model = RecordItem
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'total_amount', 'record']


    def validate(self, attrs):
        
        if attrs["pr_no"] < 0:
            raise_validation("Pr no must be a positive value")
        if attrs["pcv_no"] < 0:
            raise_validation("Pcv no must be a positive value")
        if attrs["dr_no"] < 0:
            raise_validation("Dr no must be a positive value")
        if attrs["vl"] < 0:
            raise_validation("Vl no must be a positive value")
        if attrs["po_no"] < 0:
            raise_validation("Po no must be a positive value")

        return attrs

class UpdateRecordsSerializer(serializers.ModelSerializer):

    date = serializers.DateField(input_formats=['%m/%d/%Y'], error_messages={
        "invalid": "Date must use this format: MM/DD/YYYY"
    })
    petty_cash_given = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        error_messages={
            "blank": "Petty cash given cannot be blank",
            "null": "Petty cash given cannot have null value",
            "invalid": "Invalid petty cash given value"
        }
    )
    items = UpdateRecordItemsSerializer(many=True)

    class Meta:
        model = Record
        fields = ['date', 'petty_cash_given', 'items']
        read_only_fields = ['id']

    
    def validate_petty_cash_given(self, value):

        if value < 0:
            raise_validation("Petty cash given must be a positive value")
        return value

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
            item_id = str(item_data.get("record_item_id"))

            if item_id and item_id in existing_items:
                item_instance = existing_items[item_id]

                for attr, value in item_data.items():
                    setattr(item_instance, attr, value)

                item_instance.save()

    
        total_amount_per_person = instance.items.aggregate(total=Sum('supplier_receipt_amount'))['total'] or 0
        instance.amount_site_per_person = total_amount_per_person


        remaining_amount_refunded = abs(total_amount_per_person - validated_data.get('petty_cash_given'))
        instance.amount_refunded = remaining_amount_refunded

        instance.save(update_fields=['amount_site_per_person', 'amount_refunded'])

        return instance
    

# class ImportXlslInRecordsSerializer(serializers.Serializer):

#     excel_file = serializers.FileField()

#     def validate(self, attrs):
#         file = attrs.get("excel_file")
#         if not file.name.endswith('.xlsx'):
#             raise serializers.ValidationError("Only Excel files are allowed.")
#         return attrs

#     def create(self, validated_data):

#         excel_file = validated_data["excel_file"]
#         wb = load_workbook(filename=BytesIO(excel_file.read()), data_only=True)
#         sheet = wb.active

#         # Extract the headers
#         headers = [cell.value for cell in sheet[1]]

#         grouped_data = defaultdict(list)
#         failed_imports = []
#         created_records = []


#         for row in sheet.iter_rows(min_row=2, values_only=True):
#             row_dict = dict(zip(headers, row))
#             pr_no = row_dict.get("PR No")
#             if pr_no:
#                 grouped_data[pr_no].append(row_dict)


#         # Process each group
#         for pr_no, rows in grouped_data.items():

#             try:

#                 first = rows[0]

#                 if not Record.objects.filter(pr_no=first["PR No"]).exists():

#                     record_data = {
#                         "date": first["Date"],
#                         "amount_site_per_person": first["AMOUNT/SITE. PER person"],
#                         "petty_cash_given": first["PETTY CASH GIVEN"],
#                         "amount_refunded": first["AMOUNT REFUNDED"]
#                     }

#                     items_data = [
#                         {
#                             "pr_no": row["PR NO"],
#                             "pcv_no": row['PCV NO'],
#                             "dr_no": row['DR NO'],
#                             "vl": row['VL'],
#                             "po_no": row['PO NO'],
#                             "project_site": row['PROJECT SITE'],
#                             "person_in_charge": row['PERSON IN CHARGE'],
#                             "equipment": row['EQUIPMENT'],
#                             "supplier": row['SUPPLIER'],
#                             "type_of_receipt": row['TYPE OF RECEIPT'],
#                             "invoice_receipt_no": row['INVOICE/RECEIPT NO'],
#                             "receipt_issued_to": row['RECEIPT ISSUED TO'],
#                             "qty": row['QTY'],
#                             "unit": row['UNIT'],
#                             "product_name": row['PRODUCT NAME'],
#                             "item_price": row['ITEM PRICE'],
#                             "item_unit": row['ITEM UNIT'],
#                             "total_amount": row['TOTAL AMOUNT'],
#                             "supplier_receipt_amount": row['SUPPLIER RECEIPT AMOUNT'],
#                         }
#                     for row in rows
#                     ]

#                     records = create_bulk_items(
#                         main_model=Record,
#                         child_model=RecordItem,
#                         main_data=record_data,
#                         children_data=items_data,
#                         foreign_key_name='record'
#                     )

#                     created_records.append(records)
#                 else:
#                     continue


#             except Exception as e:
#                 failed_imports.append({
#                     "pr_no": pr_no,
#                     "error": str(e)
#                 })

#         if failed_imports:
#             raise serializers.ValidationError({
#                 "message": "Some rows failed to import.",
#                 "failures": failed_imports
#             })
            
#         return created_records