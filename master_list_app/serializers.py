from rest_framework import serializers
from .models import Supplier, Product, Equipment
from quantumways.utils import is_field_empty, raise_validation, CustomCharField, CustomDecimalField
from io import BytesIO
from openpyxl import load_workbook
from collections import defaultdict
from datetime import datetime
from django.db.models import Q
from .models import EquipmentStatus, EquipmentSnapshot
import ast
from collections import Counter
from django.db.models import OuterRef, Subquery
from service_repair_app.models import ServiceRepair
from django.db import transaction
# ---------------------- SUPPLIER -----------------------------

class AddMasterListSupplierSerializer(serializers.ModelSerializer):

    # no = CustomIntegerField(
    #     blank_message="No cannot be blank",
    #     required_message="No is required"
    # )

    item = CustomCharField(
        blank_message="Item cannot be blank",
        required_message="Item is required"
    )

    class Meta:
        model = Supplier
        fields = ['item']

    def validate(self, attrs):

        # if is_field_empty(attrs["no"]):
        #     raise_validation("No cannot be blank")

        # if Supplier.objects.filter(no=attrs["no"]).exists():
        #     raise_validation(f"this No already exists")

        if is_field_empty(attrs["item"]):
            raise_validation("Item cannot be blank")
        
        return attrs
    
    def create(self, validated_data):
        return Supplier.objects.create(**validated_data)
    
class ImportxlsxInMasterListSuppliersSerializer(serializers.Serializer):

    excel_file = serializers.FileField()

    @staticmethod
    def str_to_bool(val):
        return str(val).strip().upper() == "TRUE"

    def validate(self, attrs):
        file = attrs.get("excel_file")
        if not file.name.endswith('.xlsx'):
            raise serializers.ValidationError("Only CSV files are allowed.")
        return attrs
    

    def create(self, validated_data):

        excel_file = validated_data["excel_file"]
        wb = load_workbook(filename=BytesIO(excel_file.read()), data_only=True)
        sheet = wb.active

        grouped_data = defaultdict(list)
        failed_imports = []
        created_suppliers = []


        headers = [cell.value for cell in sheet[1]]


        for rows in sheet.iter_rows(min_row=2, values_only=True):
            row_dict = dict(zip(headers, rows))
            no = row_dict.get("NO.")
            if no:
                grouped_data[no].append(row_dict)


        # Process each group
        for no, rows in grouped_data.items():
            try:

                items_data = [
                    Supplier(
                        no=row.get('NO.'),
                        item=row.get('ITEM')
                    )
                    for row in rows
                    if row.get('NO.') and not Supplier.objects.filter(no=row.get('NO.')).exists()
                ]

                created_items = Supplier.objects.bulk_create(items_data)

                created_suppliers.append(created_items)

            except Exception as e:
                failed_imports.append({
                    "no": no,
                    "error": str(e)
                })

        if failed_imports:
            raise serializers.ValidationError({
                "message": "Some rows failed to import.",
                "failures": failed_imports
            })
        
        return created_suppliers


class ViewMasterListSupplierSerializer(serializers.ModelSerializer):

    item_name = serializers.CharField(source='item')

    class Meta:
        model = Supplier
        fields = ['id', 'no', 'item_name']


class SearchMasterListSupplierSerializer(serializers.ModelSerializer):

    item_name = serializers.CharField(source='item')

    class Meta:
        model = Supplier
        fields = ['id', 'no', 'item_name']


class UpdateMasterListSupplierSerializer(serializers.ModelSerializer):

    # no = CustomIntegerField(
    #     blank_message="No cannot be blank",
    #     required_message="No is required"
    # )

    item = CustomCharField(
        blank_message="Item cannot be blank",
        required_message="Item is required"
    )

    class Meta:
        model = Supplier
        fields = ['item']

    # def validate_no(self, value):
    #     if is_field_empty(value):
    #         raise_validation("No cannot be blank")

    #     return value

    def validate_item(self, value):
        if is_field_empty(value):
            raise_validation("Item cannot be blank")
        return value

    def update(self, instance, validated_data):
        item_data = validated_data.get('item', instance.item)
        instance.item = item_data
        instance.save()
        return instance
    

# ---------------------- SUPPLIER -----------------------------

# ---------------------- PRODUCT -----------------------------
class AddMasterListProductSerializer(serializers.ModelSerializer):

    # no = serializers.IntegerField()

    item = CustomCharField(
        blank_message="Item cannot be blank",
        required_message="Item is required"
    )
    price = CustomDecimalField(
        blank_message="Price cannot be blank",
        required_message="Price is required",
        max_digits=12,
        decimal_places=2,
    )
    unit = CustomCharField(
        blank_message="Unit cannot be blank",
        required_message="Unit is required"
    )

    class Meta:
        model = Product
        fields = ['item', 'price', 'unit']

    def validate(self, attrs):

        # if is_field_empty(attrs["no"]):
        #     raise_validation("No cannot be blank")

        # if Product.objects.filter(no=attrs["no"]).exists():
        #     raise_validation(f"this No already exists")

        if attrs["price"] < 0:
            raise_validation("Price must be a positive value")

        if is_field_empty(attrs["item"]):
            raise_validation("Item cannot be blank")

        if is_field_empty(attrs["unit"]):
            raise_validation("Unit cannot be blank")
        
        return attrs
    
    def create(self, validated_data):
        return Product.objects.create(**validated_data)
    
class ViewMasterListProductSerializer(serializers.ModelSerializer):

    item_name = serializers.CharField(source='item')

    class Meta:
        model = Product
        fields = ['id', 'no', 'item_name', 'price', 'unit']

class SearchMasterListProductSerializer(serializers.ModelSerializer):

    item_name = serializers.CharField(source='item')

    class Meta:
        model = Product
        fields = ['id', 'no', 'item_name', 'price', 'unit']

class ViewMasterListDetailsProductSerializer(serializers.ModelSerializer):

    item_name = serializers.CharField(source='item')

    class Meta:
        model = Product
        fields = ['id', 'no', 'item_name', 'price', 'unit']


class UpdateMasterListProductSerializer(serializers.ModelSerializer):

    item = CustomCharField(
        blank_message="Item cannot be blank",
        required_message="Item is required"
    )
    price = CustomDecimalField(
        max_digits=12,
        decimal_places=2,
        blank_message="Price cannot be blank",
        required_message="Price is required",
    )
    unit = CustomCharField(
        blank_message="Unit cannot be blank",
        required_message="Unit is required"
    )

    class Meta:
        model = Product
        fields = ['item', 'price', 'unit']

    
    def validate_price(self, value):

        if value < 0:
            raise_validation("Price must be a positive value")

        return value

    def validate_item(self, value):
        if is_field_empty(value):
            raise_validation("Item cannot be blank")
        return value
    
    def validate_unit(self, value):
        if is_field_empty(value):
            raise_validation("Unit cannot be blank")
        return value

    def update(self, instance, validated_data):
        for attrs, value in validated_data.items():
            setattr(instance, attrs, value)
        instance.save()
        return instance
    

class ImportxlsxInMasterListProductsSerializer(serializers.Serializer):

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
        created_suppliers = []


        headers = [cell.value for cell in sheet[1]]


        for rows in sheet.iter_rows(min_row=2, values_only=True):
            row_dict = dict(zip(headers, rows))
            no = row_dict.get("NO.")
            if no:
                grouped_data[no].append(row_dict)


        for no, rows in grouped_data.items():
            try:
                items_data = [
                    Product(
                        no=row.get('NO.'),
                        item=row.get('ITEM'),
                        price=row.get('PRICE'),
                        unit=row.get('UNIT'),
                    )
                    for row in rows
                    if row.get('NO.') and not Product.objects.filter(no=row.get('NO.')).exists()
                ]

                created_items = Product.objects.bulk_create(items_data)
                created_suppliers.append(created_items)

            except Exception as e:
                failed_imports.append({
                    "no": no,
                    "error": str(e)
                })

        if failed_imports:
            raise serializers.ValidationError({
                "message": "Some rows failed to import.",
                "failures": failed_imports
            })

        return created_suppliers
    

# ---------------------- PRODUCT -----------------------------


# ---------------------- EQUIPMENT -----------------------------

class AddMasterListEquipmentSerializer(serializers.ModelSerializer):

    # no = serializers.IntegerField()

    equipment_no = CustomCharField(
        blank_message="Equipment no cannot be blank",
        required_message="Equipment no is required"
    )
    model_name = CustomCharField(
        blank_message="Model name cannot be blank",
        required_message="Model name is required"
    )
    equipment_name = CustomCharField(
        blank_message="Equipment name cannot be blank",
        required_message="Equipment name is required"
    )
    last_conduct_of_pm = serializers.DateField(
        error_messages={
            'invalid': "Last conduct of PM must use this format: YYYY-MM-DD"
        },
    )
    next_pm = serializers.DateField(
        input_formats=['%Y-%m'],
        error_messages={
            'invalid': "Next PM must use this format: YYYY-MM"
        }
    )
    remarks = CustomCharField(
        blank_message="Remarks cannot be blank",
        required_message="Remarks is required"
    )
    
    

    class Meta:
        model = Equipment
        fields = ['equipment_no', 'model_name', 'equipment_name', 'last_conduct_of_pm', 'next_pm', 'remarks']

    def to_internal_value(self, data):

        if data["last_conduct_of_pm"] in (None, "") or data["last_conduct_of_pm"].strip() == "":
            raise_validation("Last conduct of pm cannot be blank")

        if data["next_pm"] in (None, "") or data["next_pm"].strip() == "":
            raise_validation("Next pm cannot be blank")
        
        return super().to_internal_value(data)

    def validate(self, attrs):

        # if is_field_empty(attrs["no"]):
        #     raise_validation("No cannot be blank")

        # if Equipment.objects.filter(no=attrs["no"]).exists():
        #     raise_validation(f"this No already exists")

        if is_field_empty(attrs["equipment_no"]):
            raise_validation("Equipment no cannot be blank")

        if is_field_empty(attrs["model_name"]):
            raise_validation("Model name cannot be blank")

        if is_field_empty(attrs["equipment_name"]):
            raise_validation("Equipment name cannot be blank")

        if is_field_empty(attrs["remarks"]):
            raise_validation("Remarks cannot be blank")
        
        return attrs
    
    def create(self, validated_data):   
        return Equipment.objects.create(**validated_data)

class ViewMasterListEquipmentSerializer(serializers.ModelSerializer):

    last_conduct_of_pm = serializers.DateField(format='%d-%b-%Y')
    next_pm = serializers.DateField(format='%Y-%m')

    class Meta:
        model = Equipment
        fields = ['id', 'no', 'equipment_no', 'model_name', 'equipment_name', 'last_conduct_of_pm', 'next_pm', 'remarks']

class SearchMasterListEquipmentSerializer(serializers.ModelSerializer):

    last_conduct_of_pm = serializers.DateField(format='%d-%b-%Y')
    next_pm = serializers.DateField(format='%Y-%m')

    class Meta:
        model = Equipment
        fields = ['id', 'no', 'equipment_no', 'model_name', 'equipment_name', 'last_conduct_of_pm', 'next_pm', 'remarks']

class ViewMasterListDetailsEquipmentSerializer(serializers.ModelSerializer):

    last_conduct_of_pm = serializers.DateField(format='%d-%b-%Y')
    next_pm = serializers.DateField(format='%Y-%m')

    class Meta:
        model = Equipment
        fields = ['id', 'no', 'equipment_no', 'model_name', 'equipment_name', 'last_conduct_of_pm', 'next_pm', 'remarks']


class UpdateMasterListEquipmentSerializer(serializers.ModelSerializer):
    equipment_no = CustomCharField(
        blank_message="Equipment no cannot be blank",
        required_message="Equipment no is required"
    )
    model_name = CustomCharField(
        blank_message="Model name cannot be blank",
        required_message="Model name is required"
    )
    equipment_name = CustomCharField(
        blank_message="Equipment name cannot be blank",
        required_message="Equipment name is required"
    )
    last_conduct_of_pm = serializers.DateField(
        error_messages={
            'invalid': "Last conduct of PM must use this format: YYYY-MM-DD"
        }
    )
    next_pm = serializers.DateField(
        input_formats=['%Y-%m'],
        error_messages={
            'invalid': "Next PM must use this format: YYYY-MM"
        }
    )
    remarks = CustomCharField(
        blank_message="Remarks cannot be blank",
        required_message="Remarks is required"
    )

    class Meta:
        model = Equipment
        fields = ['equipment_no', 'model_name', 'equipment_name', 'last_conduct_of_pm', 'next_pm', 'remarks']

    def to_internal_value(self, data):

        if data["last_conduct_of_pm"] in (None, "") or data["last_conduct_of_pm"].strip() == "":
            raise_validation("Last conduct of pm cannot be blank")

        if data["next_pm"] in (None, "") or data["next_pm"].strip() == "":
            raise_validation("Next pm cannot be blank")
        
        return super().to_internal_value(data)

    def validate(self, attrs):

        if is_field_empty(attrs["equipment_no"]):
            raise_validation("Equipment no cannot be blank")

        if is_field_empty(attrs["model_name"]):
            raise_validation("Model name cannot be blank")

        if is_field_empty(attrs["equipment_name"]):
            raise_validation("Equipment name cannot be blank")

        if is_field_empty(attrs["remarks"]):
            raise_validation("Remarks cannot be blank")

        return attrs

    def update(self, instance, validated_data):
        for attrs, value in validated_data.items():
            setattr(instance, attrs, value)
        instance.save()
        return instance
    

class ImportxlsxInMasterListEquipmentsSerializer(serializers.Serializer):

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
        created_equipments = []


        headers = [cell.value for cell in sheet[1]]

        for rows in sheet.iter_rows(min_row=2, values_only=True):
            row_dict = dict(zip(headers, rows))
            no = row_dict.get("#")
            if no:
                grouped_data[no].append(row_dict)

        # Process each group
        for no, rows in grouped_data.items():
            try:


                items_data = [
                    Equipment(
                        no=row.get('#'),
                        equipment_no=row.get('Equipment No.'),
                        model_name=row.get('Model Name'),
                        equipment_name=row.get('Equipment Name'),
                        last_conduct_of_pm=datetime.strptime(row.get('Last Conduct of PM'), '%d-%b-%Y').date(),
                        next_pm=datetime.strptime(row.get('Next PM'), '%B-%Y').date(),
                        remarks=row.get('Remarks')
                    )
                    for row in rows
                    if row.get('#') and not Equipment.objects.filter(no=row.get('#')).exists()
                ]

 

                created_items = Equipment.objects.bulk_create(items_data)

                created_equipments.append(created_items)

            except Exception as e:
                failed_imports.append({
                    "no": no,
                    "error": str(e)
                })

        if failed_imports:
            raise serializers.ValidationError({
                "message": "Some rows failed to import.",
                "failures": failed_imports
            })
        
        return created_equipments
    

# ---------------------- EQUIPMENT -----------------------------
class ExistingSupplierMasterListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Supplier
        fields = ['item']

class ExistingProductMasterListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = ['item']



# ---------------------- EQUIPMENT V2 ----------------------------------

class ImportxlsxInMasterListEquipmentsV2Serializer(serializers.Serializer):

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
        seen_failures = set()
        created_equipments = []


        headers = [cell.value for cell in sheet[1]]

        for rows in sheet.iter_rows(min_row=2, values_only=True):
            row_dict = dict(zip(headers, rows))
            equipment = row_dict.get("EQUIPMENT")
            if equipment:
                grouped_data[equipment].append(row_dict)
        # Process each group
        for _, rows in grouped_data.items():

            items_data = []

            try:
                
                for row in rows:

                    service_rendered_raw = row.get('SERVICE RENDERED')
                    if isinstance(service_rendered_raw, str) and service_rendered_raw.strip():
                        service_rendered_list = [
                            part.strip().upper()
                            for part in service_rendered_raw.split(",")
                            if part.strip()
                        ]
                    else:
                        service_rendered_list = []

                    problems_encountered_raw = row.get('PROBLEMS ENCOUNTERED')

                    if isinstance(problems_encountered_raw, str):
                        problems_encountered_list = [x.strip() for x in problems_encountered_raw.split(",")]
                    else:
                        problems_encountered_list = []

                    eq_no = row.get('EQUIPMENT NO.')

                    if eq_no:
                        if eq_no and not Equipment.objects.filter(equipment_no=row.get('EQUIPMENT NO.')).exists():
                            items_data.append(
                                Equipment(
                                    equipment=str(row.get('EQUIPMENT')).lower(),
                                    brand_name=str(row.get('BRAND NAME')).lower(),
                                    equipment_no=row.get('EQUIPMENT NO.'),
                                    status=str(row.get('STATUS')).lower(),
                                    plate_no=row.get('PLATE NO'),
                                    site=str(row.get('SITE')).lower(),
                                    color=str(row.get('COLOR')).lower(),
                                    chasis_no=str(row.get('CHASIS NO')).lower(),
                                    model=row.get('MODEL'),
                                    last_inspection=datetime.strptime(row.get('LAST INSPECTION'), '%d-%b-%Y').date(),
                                    last_registration=datetime.strptime(row.get('LAST REGISTRATION'), '%d-%b-%Y').date(),
                                    next_registration=datetime.strptime(row.get('NEXT REGISTRATION'), '%d-%b-%Y').date(),
                                    last_conduct_of_pm=datetime.strptime(row.get('LAST CONDUCT OF PM'), '%d-%b-%Y').date(),
                                    next_pm=datetime.strptime(row.get('NEXT PM'), '%d-%b-%Y').date(),
                                    service_rendered=service_rendered_list,
                                    problems_encountered=problems_encountered_list,
                                    materials_purchased=str(row.get('MATERIALS PURCHASED')).lower(),
                                    quantity=row.get('QUANTITY'),
                                    mechanic=str(row.get('MECHANIC')).lower(),
                                    sr_no=str(row.get('SR NO')).upper(),
                                    remarks=str(row.get('REMARKS')).lower(),
                                    is_created_equipment=False
                                )
                            )
                        else:
                            if eq_no not in seen_failures:
                                failed_imports.append({
                                    "equipment_no": eq_no,
                                    "error": "Already exists"
                                })
                                seen_failures.add(eq_no)

                created_items = Equipment.objects.bulk_create(items_data)

                created_equipments.extend(created_items)

                print(len(created_items))

                equipment_map = defaultdict(list)

                # Build equipment map for M2M Linking
                for equipment in created_items:
                    key = (equipment.sr_no)
                    if key:
                        equipment_map[key].append(equipment.pk)
                

                original_ids = {}

                # Snapshot comparison: mark originals
                for snap in EquipmentSnapshot.objects.order_by('created_at').filter(is_created_equipment=True):
                    try:
                        
                        if snap.sr_no:
                            print(f"SR NO EXIST")
                            # Find all imported rows with the same sr no
                            matches = Equipment.objects.order_by('created_at').filter(sr_no=snap.sr_no, is_created_equipment=False)
                        else:
                            print(f"SR NO NOT EXIST")
                            # If sr_no is empty/null, match by equipment_no
                            matches = Equipment.objects.filter(
                                Q(sr_no__isnull=True) | Q(sr_no=None) | Q(sr_no="N/A"),
                                equipment_no__iexact=snap.equipment_no
                            )

                        if matches.exists():
                            print(f"Matches exists run!")
                            eq = matches.first()
                            
                            if snap.sr_no:
                                original_ids[eq.sr_no] = (eq.pk, snap)
                            else:
                                original_ids[eq.equipment_no] = (eq.pk, snap)

                
                    except EquipmentSnapshot.DoesNotExist:
                        pass
                    
                for _, (pk, snap) in original_ids.items():
                    
                    print(f"PK: {pk}")

                    Equipment.objects.filter(pk=pk).update(
                        is_created_equipment=True
                    )

                
                # Relink M2M
                try:
                    with transaction.atomic():
                        for sr_key, eq_pks in equipment_map.items():
                            try:
                                service_repair = ServiceRepair.objects.get(sr_no=sr_key)
                            except ServiceRepair.DoesNotExist:
                                continue
                            # Relink M2M
                            service_repair.equipments.add(*eq_pks)
                except Exception as e:
                    raise_validation(e)

            except Exception as e:
                raise_validation(e)

        if failed_imports:
            raise_validation(failed_imports)
        
        return created_equipments


class StrictCharField(serializers.CharField):

    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail("invalid")
        return super().to_internal_value(data)
    
class StrictIntegerField(serializers.IntegerField):

    def to_internal_value(self, data):
        if not isinstance(data, int):
            self.fail("invalid")
        return super().to_internal_value(data)


class CreateEquipmentV2Serializer(serializers.ModelSerializer):
    
    equipment = serializers.CharField(
        error_messages={
            "blank": "Equipment cannot be blank",
            "null": "Equipment must not be null",
            "invalid": "Invalid equipment value"
        }
    )
    brand_name = serializers.CharField(
        error_messages={
            "blank": "Brand name cannot be blank",
            "null": "Brand name must not be null",
            "invalid": "Invalid brand name value"
        }
    )
    equipment_no = serializers.CharField(
        error_messages={
            "blank": "Equipment no cannot be blank",
            "null": "Equipment no must not be null",
            "invalid": "Invalid equipment no value"
        }
    )

    status = serializers.CharField(
        error_messages={
            "blank": "Status cannot be blank",
            "invalid": "Invalid status",
            "null": "Status cannot be null",
        }
    )

    plate_no = serializers.CharField(
        error_messages={
            "blank": "Plate no cannot be blank",
            "null": "Plate no must not be null",
            "invalid": "Invalid Plate no value"
        }
    )

    site = serializers.CharField(
        error_messages={
            "blank": "Site cannot be blank",
            "null": "Site must not be null",
            "invalid": "Invalid site value"
        }
    )

    color = serializers.CharField(
        error_messages={
            "blank": "Color cannot be blank",
            "null": "Color must not be null",
            "invalid": "Invalid color value"
        }
    )

    chasis_no = serializers.CharField(
        error_messages={
            "blank": "Chasis no cannot be blank",
            "null": "Chasis no must not be null",
            "invalid": "Invalid chasis no value"
        }
    )

    model = serializers.CharField(
        error_messages={
            "blank": "Model cannot be blank",
            "null": "Model cannot be null"
        }
    )

    last_inspection = serializers.DateField(
        allow_null=True,
        input_formats=['%d-%b-%Y', '%Y-%m-%d'],
        error_messages={
            "invalid": "Invalid inspection date format: Use (dd-MMM-YYYY), e.g. 24-Oct-2025",
        }
    )
    last_registration = serializers.DateField(
        allow_null=True,
        input_formats=['%d-%b-%Y', '%Y-%m-%d'],
        error_messages={
            "invalid": "Invalid last registration format: Use (dd-MMM-YYYY), e.g. 24-Oct-2025",
        }
    )

    next_registration = serializers.DateField(
        allow_null=True,
        input_formats=['%d-%b-%Y', '%Y-%m-%d'],
        error_messages={
            "invalid": "Invalid next registration format: Use (dd-MMM-YYYY), e.g. 24-Oct-2025",
        }
    )

    last_conduct_of_pm = serializers.DateField(
        allow_null=True,
        input_formats=['%d-%b-%Y', '%Y-%m-%d'],
        error_messages={
            "invalid": "Invalid last conduct of pm format: Use (dd-MMM-YYYY), e.g. 24-Oct-2025",
        }
    )

    next_pm = serializers.DateField(
        allow_null=True,
        input_formats=['%d-%b-%Y', '%Y-%m-%d'],
        error_messages={
            "invalid": "Invalid next pm format: Use (dd-MMM-YYYY), e.g. 24-Oct-2025",
        }
    )
    
    service_rendered = serializers.ListField(
        child=serializers.CharField(
            allow_blank=True,
            allow_null=True,
            required=False,
        ),
    )

    problems_encountered = serializers.ListField(
        child=serializers.CharField(
            allow_blank=True,
            allow_null=True,
            required=False,
        ),
    )
    # problems_encountered = serializers.CharField(
    #     allow_blank=True,
    #     allow_null=True,
    #     required=False,
    # )

    materials_purchased = serializers.CharField(
        allow_blank=True,
        allow_null=True,
        required=False,
    )

    quantity = serializers.IntegerField(
        allow_null=True,
        required=False,
    )

    mechanic = serializers.CharField(
        allow_blank=True,
        allow_null=True,
        required=False,
    )

    remarks = serializers.CharField(
        allow_blank=True,
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Equipment
        fields = '__all__'

    def validate(self, attrs):
        
        # if Equipment.objects.filter(equipment_no=attrs["equipment_no"]).exists():
        #     raise_validation(f"Equipment no {attrs["equipment_no"]} already exists")

        # if Equipment.objects.filter(equipment_no=attrs["chasis_no"]).exists():
        #     raise_validation(f"Chasis no {attrs["chasis_no"]} already exists")

        # if Equipment.objects.filter(equipment_no=attrs["plate_no"]).exists():
        #     raise_validation(f"Plate no {attrs["plate_no"]} already exists")

        if attrs["status"] not in EquipmentStatus.AVAILABLE_STATUS_CHOICES:
            raise_validation("Invalid status")

        if attrs["quantity"] < 0:
            raise_validation("Quantity cannot have negative value")

        return attrs

    def create(self, validated_data):
        equipment = str(validated_data.pop('equipment')).lower()
        equipment_obj = Equipment.objects.create(equipment=equipment, is_created_equipment=True, **validated_data)

        return equipment_obj
    

class ListEquipmentV2Serializer(serializers.ModelSerializer):

    class Meta:
        model = Equipment
        fields = [
            'id', 'equipment_no', 'equipment', 'plate_no',
            'chasis_no', 'model', 'status'
        ]

class ListEquipmentDetailsV2Serializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data.pop('created_at')
        data.pop('updated_at')
        data.pop('no')
        data.pop('equipment_name')
        data.pop('model_name')
        data.pop('is_created_equipment')
        data.pop('sr_no')
        return data

    class Meta:
        model = Equipment
        fields = '__all__'

class ListGroupEquipmentDetailsV2Serializer(serializers.ModelSerializer):
    
    grouped_data = serializers.SerializerMethodField()

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

    def get_grouped_data(self, obj):

        equipment_id = self.context.get('id')
        selected_equipment = Equipment.objects.get(id=equipment_id)

        latest_status_subquery = (
            Equipment.objects.filter(
                equipment=OuterRef('equipment'),
                equipment_no=OuterRef("equipment_no")
            )
            .order_by('-updated_at')
            .values('status')[:1]
        )

        # All equipments with the same name (Self Loading Truck) and same equipment no
        equipments = (
            Equipment.objects.filter(
                equipment__iexact=selected_equipment.equipment
            )
            .filter(equipment_no__iexact=selected_equipment.equipment_no)
            .annotate(latest_status=Subquery(latest_status_subquery)).order_by('created_at')
        )

        fields = [
            "equipment", "brand_name", "equipment_no", "status", "plate_no", "site", "color",
            "chasis_no", "model", "date", "sr_no", "repair_no"
        ]

        show_once = self.once_displayed(equipments, fields)
        grouped_data = defaultdict(list)

        for equipment in equipments:
            is_latest = (equipment.latest_status == equipment.status)
            status_value = equipment.latest_status if is_latest else None

            sr_queryset = equipment.service_repairs.all()

            if sr_queryset.exists():
                for sr in sr_queryset:
                    grouped_data[equipment.equipment_no].append({
                        "id": equipment.id,
                        "equipment": show_once("equipment", equipment.equipment),
                        "equipment_no": show_once("equipment_no", equipment.equipment_no),
                        "status": show_once("status", status_value),
                        "plate_no": show_once("plate_no", equipment.plate_no),
                        "site": show_once("site", equipment.site),
                        "color": show_once("color", equipment.color),
                        "chasis_no": show_once("chasis_no", equipment.chasis_no),
                        "brand_name": show_once("brand_name", equipment.brand_name),
                        "model": show_once("model", equipment.model),
                        "last_inspection": equipment.last_inspection,
                        "last_registration": equipment.last_registration,
                        "next_registration": equipment.next_registration,
                        "last_conduct_of_pm": equipment.last_conduct_of_pm,
                        "next_pm": equipment.next_pm,
                        "service_rendered": equipment.service_rendered,
                        "date": sr.date,
                        "srf_number": sr.sr_no,
                        "rf_number": sr.repair_no,
                        "problems_encountered": equipment.problems_encountered,
                        "materials_purchased": equipment.materials_purchased,
                        "quantity": equipment.quantity,
                        "mechanic": equipment.mechanic,
                        "remarks": equipment.remarks
                    })
            else:
                grouped_data[equipment.equipment_no].append({
                    "id": equipment.id,
                    "equipment": show_once("equipment", equipment.equipment),
                    "equipment_no": show_once("equipment_no", equipment.equipment_no),
                    "status": show_once("status", status_value),
                    "plate_no": show_once("plate_no", equipment.plate_no),
                    "site": show_once("site", equipment.site),
                    "color": show_once("color", equipment.color),
                    "chasis_no": show_once("chasis_no", equipment.chasis_no),
                    "brand_name": show_once("brand_name", equipment.brand_name),
                    "model": show_once("model", equipment.model),
                    "last_inspection": equipment.last_inspection,
                    "last_registration": equipment.last_registration,
                    "next_registration": equipment.next_registration,
                    "last_conduct_of_pm": equipment.last_conduct_of_pm,
                    "next_pm": equipment.next_pm,
                    "service_rendered": equipment.service_rendered,
                    "date": None,
                    "srf_number": None,
                    "rf_number": None,
                    "problems_encountered": equipment.problems_encountered,
                    "materials_purchased": equipment.materials_purchased,
                    "quantity": equipment.quantity,
                    "mechanic": equipment.mechanic,
                    "remarks": equipment.remarks
                })

        # Flatten grouped entries into a single list
        final_result = [item for group in grouped_data.values() for item in group]
        return final_result

    class Meta:
        model = Equipment
        fields = [
            'grouped_data'
        ]

class UpdateMasterlistEquipmentV2Serializer(serializers.ModelSerializer):

    equipment = serializers.CharField(
        error_messages={
            "blank": "Equipment cannot be blank",
            "null": "Equipment must not be null",
            "invalid": "Invalid equipment value"
        }
    )
    brand_name = serializers.CharField(
        error_messages={
            "blank": "Brand name cannot be blank",
            "null": "Brand name must not be null",
            "invalid": "Invalid brand name value"
        }
    )
    equipment_no = serializers.CharField(
        error_messages={
            "blank": "Equipment no cannot be blank",
            "null": "Equipment no must not be null",
            "invalid": "Invalid equipment no value"
        }
    )

    status = serializers.CharField(
        error_messages={
            "blank": "Status cannot be blank",
            "invalid": "Invalid status",
            "null": "Status cannot be null",
        }
    )

    plate_no = serializers.CharField(
        error_messages={
            "blank": "Plate no cannot be blank",
            "null": "Plate no must not be null",
            "invalid": "Invalid Plate no value"
        }
    )

    site = serializers.CharField(
        error_messages={
            "blank": "Site cannot be blank",
            "null": "Site must not be null",
            "invalid": "Invalid site value"
        }
    )

    color = serializers.CharField(
        error_messages={
            "blank": "Color cannot be blank",
            "null": "Color must not be null",
            "invalid": "Invalid color value"
        }
    )

    chasis_no = serializers.CharField(
        error_messages={
            "blank": "Chasis no cannot be blank",
            "null": "Chasis no must not be null",
            "invalid": "Invalid chasis no value"
        }
    )

    model = serializers.CharField(
        error_messages={
            "blank": "Model cannot be blank",
            "null": "Model cannot be null"
        }
    )

    last_inspection = serializers.DateField(
        allow_null=True,
        input_formats=['%d-%b-%Y', '%Y-%m-%d'],
        error_messages={
            "invalid": "Invalid inspection date format: Use (dd-MMM-YYYY), e.g. 24-Oct-2025",
        }
    )
    last_registration = serializers.DateField(
        allow_null=True,
        input_formats=['%d-%b-%Y', '%Y-%m-%d'],
        error_messages={
            "invalid": "Invalid last registration format: Use (dd-MMM-YYYY), e.g. 24-Oct-2025",
        }
    )

    next_registration = serializers.DateField(
        allow_null=True,
        input_formats=['%d-%b-%Y', '%Y-%m-%d'],
        error_messages={
            "invalid": "Invalid next registration format: Use (dd-MMM-YYYY), e.g. 24-Oct-2025",
        }
    )

    last_conduct_of_pm = serializers.DateField(
        allow_null=True,
        input_formats=['%d-%b-%Y', '%Y-%m-%d'],
        error_messages={
            "invalid": "Invalid last conduct of pm format: Use (dd-MMM-YYYY), e.g. 24-Oct-2025",
        }
    )

    next_pm = serializers.DateField(
        allow_null=True,
        input_formats=['%d-%b-%Y', '%Y-%m-%d'],
        error_messages={
            "invalid": "Invalid next pm format: Use (dd-MMM-YYYY), e.g. 24-Oct-2025",
        }
    )
    
    service_rendered = serializers.ListField(
        child=serializers.CharField(
            allow_blank=True,
            allow_null=True,
            required=False,
        ),
    )

    problems_encountered = serializers.ListField(
        child=serializers.CharField(
            allow_blank=True,
            allow_null=True,
            required=False,
        ),
    )

    materials_purchased = serializers.CharField(
        allow_blank=True,
        allow_null=True,
        required=False,
    )

    quantity = serializers.IntegerField(
        allow_null=True,
        required=False,
    )

    mechanic = serializers.CharField(
        allow_blank=True,
        allow_null=True,
        required=False,
    )

    remarks = serializers.CharField(
        allow_blank=True,
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Equipment
        fields = [
            "equipment", "brand_name", "equipment_no", "status", "plate_no",
            "site", "color", "chasis_no", "model", "last_inspection", "last_registration",
            "next_registration", "last_conduct_of_pm", "next_pm",
            "service_rendered", "problems_encountered", "materials_purchased", "quantity",
            "mechanic", "remarks"
        ]

    def validate(self, attrs):

        if attrs["status"] not in EquipmentStatus.AVAILABLE_STATUS_CHOICES:
            raise_validation("Invalid status")

        if attrs["quantity"] < 0:
            raise_validation("Quantity cannot have negative value")

        return attrs

    def update(self, instance, validated_data):
        
        # if "status" in validated_data and instance.status != validated_data["status"]:
        #     print(f"Status lang ang nababago")
        #     new_status = validated_data.pop('status')

        #     # Bulk update status for all records with the same equipment_no
        #     self.Meta.model.objects.filter(
        #         equipment__iexact=instance.equipment,
        #         equipment_no__iexact=instance.equipment_no
        #     ).update(status=new_status)

        #     instance.status = new_status
        #     return instance
        
        # print(f"MAY NABAGO SA IBANG FIELDS")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class DropdownItemEquipmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Equipment
        fields = ['equipment']


    def to_representation(self, instance):
        
        data = super().to_representation(instance)

        data["equipment"] = str(data["equipment"]).lower()

        return data
    

class EquipmentLookupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Equipment
        fields = ['color']

class DropdownSerialEquipmentNumberSerializer(serializers.ModelSerializer):


    class Meta:
        model = Equipment
        fields = ['equipment_no']


# Import equipment V3

class ImportxlsxInMasterListEquipmentsV3Serializer(serializers.Serializer):

    excel_file = serializers.FileField()

    @staticmethod
    def str_to_bool(val):
        return str(val).strip().upper() == "TRUE"

    def validate(self, attrs):
        file = attrs.get("excel_file")
        if not file.name.endswith('.xlsx'):
            raise serializers.ValidationError("Only Excel files are allowed.")
        return attrs
    
    def parse_to_list(self, value):
        if value:
            return [x.strip() for x in value.split(",") if x.strip()]
        return []

    def create(self, validated_data):

        excel_file = validated_data["excel_file"]

        wb = load_workbook(filename=BytesIO(excel_file.read()), data_only=True)
        sheet = wb.active

        grouped_data = defaultdict(list)
        failed_imports = []
        seen_failures = set()
        created_equipments = []
        is_seen = defaultdict(list)


        headers = [cell.value for cell in sheet[1]]

        for rows in sheet.iter_rows(min_row=2, values_only=True):
            row_dict = dict(zip(headers, rows))
            equipment = row_dict.get("EQUIPMENT")
            if equipment:
                grouped_data[equipment].append(row_dict)
        # Process each group
        for _, rows in grouped_data.items():

            items_data = []

            try:
                
                for row in rows:

                    eq_no = row.get('EQUIPMENT NO.')

                    if eq_no and not Equipment.objects.filter(equipment_no=row.get('EQUIPMENT NO.')).exists():
                        items_data.append(
                            Equipment(
                                equipment=str(row.get('EQUIPMENT')).lower(),
                                brand_name=str(row.get('BRAND NAME')).lower(),
                                equipment_no=row.get('EQUIPMENT NO.'),
                                status=str(row.get('STATUS')).lower(),
                                plate_no=row.get('PLATE NO'),
                                site=str(row.get('SITE')).lower(),
                                color=str(row.get('COLOR')).lower(),
                                chasis_no=str(row.get('CHASIS NO')).lower(),
                                model=row.get('MODEL'),
                                last_inspection=datetime.strptime(row.get('LAST INSPECTION'), '%d-%b-%Y').date(),
                                last_registration=datetime.strptime(row.get('LAST REGISTRATION'), '%d-%b-%Y').date(),
                                next_registration=datetime.strptime(row.get('NEXT REGISTRATION'), '%d-%b-%Y').date(),
                                last_conduct_of_pm=datetime.strptime(row.get('LAST CONDUCT OF PM'), '%d-%b-%Y').date(),
                                next_pm=datetime.strptime(row.get('NEXT PM'), '%d-%b-%Y').date(),
                                service_rendered=self.parse_to_list(str(row.get('SERVICE RENDERED'))),
                                problems_encountered=self.parse_to_list(str(row.get('PROBLEMS ENCOUNTERED'))),
                                materials_purchased=row.get('MATERIALS PURCHASED'),
                                quantity=row.get('QUANTITY'),
                                mechanic=row.get('MECHANIC'),
                                remarks=row.get('REMARKS'),
                                is_created_equipment=True
                            )
                        )
                    else:
                        if eq_no not in seen_failures:
                            failed_imports.append({
                                "equipment_no": eq_no,
                                "error": "Already exists"
                            })
                            seen_failures.add(eq_no)

                created_items = Equipment.objects.bulk_create(items_data)

                created_equipments.extend(created_items)

                equipment_map = defaultdict(list)

                # Build equipment map for M2M Linking
                for equipment in created_items:
                    key = (equipment.sr_no)
                    if key:
                        equipment_map[key].append(equipment.pk)
                
                # Relink M2M
                try:
                    with transaction.atomic():
                        for sr_key, eq_pks in equipment_map.items():
                            try:
                                service_repair = ServiceRepair.objects.get(sr_no=sr_key)
                            except ServiceRepair.DoesNotExist:
                                continue
                            # Relink M2M
                            service_repair.equipments.add(*eq_pks)
                except Exception as e:
                    raise_validation(e)

            except Exception as e:
                raise_validation(e)

        if failed_imports:
            raise_validation(failed_imports)
        
        return created_equipments
# Import equipment V3