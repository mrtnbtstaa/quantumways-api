from collections import defaultdict
from datetime import datetime
from io import BytesIO
from openpyxl import load_workbook
from rest_framework import serializers
from quantumways.utils import raise_validation
from .models import ServiceRepair, EquipmentLog, Material, ServiceChoices
from django.db import transaction
from quantumways.services.services import create_bulk_items
from master_list_app.models import Equipment
import ast
from django.db.models import OuterRef, Subquery

class StrictCharField(serializers.CharField):

    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail("invalid")
        return super().to_internal_value(data)

class CreateEquipmentLogsSerializer(serializers.ModelSerializer):

    status = StrictCharField(
        error_messages={
            "required": "Status is required",
            "blank": "Status must not be blank",
        }
    )
    action_type = StrictCharField(
        error_messages={
            "blank": "Action type is required",
            "required": "Action type is required"
        }
    )
    action_date = serializers.DateField(
        input_formats=['%d-%m-%Y'],
        error_messages={
            "invalid": f"Invalid date format use this instead: DD-MM-YYYY",
            "null": "date cannot be null"
        }
    )
    last_repaired = serializers.DateField(
        input_formats=['%d-%m-%Y'],
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "Invalid last repaired format use this instead: DD-MM-YYYY",
        }
    )
    last_replacement = serializers.DateField(
        input_formats=['%d-%m-%Y'],
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "Invalid last replacement format use this instead: DD-MM-YYYY"
        }
    )
    last_maintenance = serializers.DateField(
        input_formats=['%d-%m-%Y'],
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "Invalid last maintenance format use this instead: DD-MM-YYYY"
        }
    )
    problems_encountered = StrictCharField(
        allow_blank=True,
        allow_null=True
    )
    works_service_done = serializers.ListField(
        child=StrictCharField(
            error_messages={
                "required": "Works/Service done is required",
                "blank": "Works/Service done must not be blank"
            }
        )
    )

    class Meta:
        model = EquipmentLog
        fields = [
            'status', 'transferred_to', 'action_type',
            'action_date', 'last_repaired', 'last_replacement',
            'last_maintenance', 'problems_encountered', 'works_service_done'
        ]

    def validate(self, attrs):

        status = attrs.get('status', None)

        transferred_to = attrs.get('transferred_to', None)

        STATUS_CHOICES = [ServiceChoices.NEW, ServiceChoices.OLD, ServiceChoices.TRANSFERRED]

        if status not in STATUS_CHOICES:
            raise_validation("Invalid status")

        if status == ServiceChoices.TRANSFERRED and not transferred_to:
            raise_validation("Both transffered to value must be present")

        return attrs
    
class CreateMaterialSerializer(serializers.ModelSerializer):

    items = serializers.CharField(
        error_messages={
            "required": "Items is required",
            "blank": "Items must not be blank"
        }
    )

    quantity = serializers.IntegerField(
        error_messages={
            "required": "Quantity is required",
            "blank": "Quantity must not be blank",
            "invalid": "Quantity must be a number",
            "null": "Quantity must not be null"
        }
    )

    class Meta:
        model = Material
        fields = ['items', 'quantity']


    def validate_quantity(self, value):
        if value < 0:
            raise_validation("Quantity must be a positive value")
        return value


class CreateServiceRepairSerializer(serializers.ModelSerializer):   

    sr_no = StrictCharField(
        required=True,
        allow_blank=False,
        allow_null=False,
        error_messages={
            "required": "Sr no is required",
            "blank": "Sr no cannot must not be blank",
            "null": "Sr no cannot be null"
        }
    )
    repair_no = StrictCharField(
        error_messages={
            "required": "Repair no is required",
            "blank": "Repair no must not be blank",
            "null": "Repair no cannot be null"
        }
    )
    date = serializers.DateField(
        input_formats=['%d-%m-%Y'],
        error_messages={
            "invalid": "Invalid date format use this instead: DD-MM-YYYY",
            "null": "Date cannot be null"
        }
    )
    site = StrictCharField(
        error_messages={
            "required": "Site is required",
            "blank": "Site must not be blank",
            "null": "Site cannot be null"
        }
    )
    tools_equipment = StrictCharField(
        error_messages={
            "required": "Tools/Equipment is required",
            "blank": "Tools/Equipment must not be blank",
            "null": "Tools/Equipment cannot be null"
        }
    )
    serial_equipment_number = StrictCharField(
        error_messages={
            "required": "Serial/Equipment Number is required",
            "blank": "Serial/Equipment Number must not be blank",
            "null": "Serial/Equipment Number cannot be null"
        }
    )
    color = StrictCharField(
        error_messages={
            "required": "Color is required",
            "blank": "Color must not be blank",
            "null": "Color cannot be null"
        }
    )

    repaired_by = StrictCharField(
        error_messages={
            "required": "Repaired by is required",
            "blank": "Repaired by cannot be blank",
            "null": "Repaired by cannot be blank"
        }
    )

    equipment_log = CreateEquipmentLogsSerializer(many=False)

    materials = CreateMaterialSerializer(many=True)

    date_started = serializers.DateField(
        allow_null=True,
        input_formats=['%d-%m-%Y'],
        error_messages={
            "invalid": "invalid date started format use this instead: DD-MM-YYYY",
            "null": "Date started cannot be null"
        }
    )
    date_completed = serializers.DateField(
        allow_null=True,
        input_formats=['%d-%m-%Y'],
        error_messages={
            "invalid": "invalid date completed format use this instead: DD-MM-YYYY",
            "null": "Date completed cannot be null"
        }
    )
    remarks = StrictCharField(
        allow_blank=True,
        allow_null=True,
        required=False,
        error_messages={
            "required": "Remarks is required",
            "blank": "Remarks must not be blank"
        }
    )
    requested_by = StrictCharField(
        error_messages={
            "required": "Requested by is required",
            "blank": "Requested by must not be blank",
            "null": "Requested by cannot be null"
        }
    )
    noted_by = StrictCharField(
        error_messages={
            "required": "Notes by is required",
            "blank": "Notes by must not be blank",
            "null": "Noted by cannot be null"
        }
    )
    approved_by = StrictCharField(
        error_messages={
            "required": "Approved by by is required",
            "blank": "Approved by by must not be blank",
            "null": "Approved by cannot be null"
        }
    )
 

    class Meta:
        model = ServiceRepair
        fields = [
            'sr_no', 'repair_no', 'date', 'site',
            'tools_equipment', 'serial_equipment_number', 'color', 'repaired_by',
            'equipment_log', 'materials', 'date_started', 'date_completed',
            'remarks', 'requested_by', 'noted_by', 'approved_by'
        ]

    def validate(self, attrs):
        
        if not Equipment.objects.filter(equipment_no__iexact=attrs.get('serial_equipment_number')).exists():
            raise_validation("No Serial equipment number found")

        if not Equipment.objects.filter(equipment__iexact=attrs.get('tools_equipment')).exists():
            raise_validation("No tools equipment found")

        return attrs


    def create(self, validated_data):
        
        # Get the first equipment based on serial number
        equipment_instance = Equipment.objects.filter(
            equipment_no=validated_data.get('serial_equipment_number')
        ).first()

        if not equipment_instance:
            raise_validation("No equipment found with this serial number")

        # Extract the nested serializers
        equipment_log_data = validated_data.pop('equipment_log')

        materials_data = validated_data.pop('materials')

        # Mapped data
        mapped_data = {
            "equipment": equipment_instance.equipment.lower() or str(validated_data.get("tools_equipment", "")).lower(),
            "brand_name": equipment_instance.brand_name if equipment_instance.brand_name else None,
            "equipment_no": equipment_instance.equipment_no,
            "status": equipment_instance.status,
            "plate_no": equipment_instance.plate_no,
            "site": equipment_instance.site,
            "color": equipment_instance.color ,
            "chasis_no": equipment_instance.chasis_no,
            "model": equipment_instance.model,
            "last_inspection": equipment_instance.last_inspection,
            "last_registration": equipment_instance.last_registration,
            "next_registration": equipment_instance.next_registration,
            "last_conduct_of_pm": equipment_instance.last_conduct_of_pm,
            "next_pm": equipment_instance.next_pm,
            "service_rendered": equipment_log_data.get("works_service_done") if isinstance(equipment_log_data.get("works_service_done"), list) else equipment_instance.service_rendered,
            "problems_encountered": equipment_instance.problems_encountered if equipment_instance.problems_encountered else equipment_log_data.get("problems_encountered"),
            "mechanic": equipment_instance.mechanic if equipment_instance.mechanic else validated_data.get("repaired_by"),
            "remarks": equipment_instance.remarks if equipment_instance.remarks else validated_data.get("remarks")
        }

        # original_equipment_isnull = Equipment.objects.filter(sr_no__isnull=True, is_created_equipment=True).first()

        # if original_equipment_isnull:
        #     original_equipment_update = (
        #         Equipment.objects.filter(
        #             equipment_no=validated_data.get('serial_equipment_number'),
        #             is_created_equipment=True)
        #             .update(
        #                 sr_no=validated_data.get('sr_no', None)
        #             )
        #         )


        # problems_encountered=mapped_data.get('problems_encountered', None),
        # service_rendered=mapped_data.get('service_rendered', []),
        # materials_purchased=materials_data[0].get('items', None),
        # mechanic=mapped_data.get('mechanic', None),
        # remarks=mapped_data.get('remarks', None)

        
        equipment_pks_to_link = set()

        is_master_equipment_already_linked = ServiceRepair.objects.filter(
            equipments=equipment_instance
        ).exists()

        if not is_master_equipment_already_linked:
            equipment_pks_to_link.add(equipment_instance.pk)


        for material_data in materials_data:

            equipment = Equipment.objects.create(
                **mapped_data,
                sr_no=validated_data.get('sr_no', None),
                materials_purchased=material_data.get('items', None),
                quantity=material_data.get('quantity', 0),
                is_created_equipment=False
            )

            equipment_pks_to_link.add(equipment.pk)

        try:

            with transaction.atomic():
                
                service_repair = create_bulk_items(
                    main_model=ServiceRepair,
                    child_model=Material,
                    main_data=validated_data,
                    children_data=materials_data,
                    foreign_key_name='service_repair'
                )

                service_repair.equipments.set(list(equipment_pks_to_link))

                EquipmentLog.objects.create(**equipment_log_data, service_repair=service_repair)

                return service_repair

                
        except Exception as e:
            raise_validation(f"Something went wrong with the transaction: {e}")


class ListEquipmentLogSerializer(serializers.ModelSerializer):

    equipment_log_id = serializers.UUIDField(source='id')
    action_date = serializers.DateField(format='%d-%m-%Y')
    last_repaired = serializers.DateField(format='%d-%m-%Y')
    last_replacement = serializers.DateField(format='%d-%m-%Y')
    last_maintenance = serializers.DateField(format='%d-%m-%Y')
    works_service_done = serializers.SerializerMethodField()

    def get_works_service_done(self, obj):
        if isinstance(obj.works_service_done, str):
            # convert string representation of list to actual list
            return ast.literal_eval(obj.works_service_done)
        return obj.works_service_done

    class Meta:
        model = EquipmentLog
        fields = [
            'equipment_log_id' ,'status', 'transferred_to',
            'action_type', 'action_date', 'last_repaired',
            'last_replacement', 'last_maintenance',
            'problems_encountered', 'works_service_done'
        ]

class ListMaterialSerializer(serializers.ModelSerializer):

    material_id = serializers.UUIDField(source='id')

    class Meta:
        model = Material
        fields = ['material_id' ,'items', 'quantity']


class ListServiceRepairSerializer(serializers.ModelSerializer):

    service_repair_id = serializers.UUIDField(source='id')
    equipment_no = serializers.CharField(source='serial_equipment_number')

    class Meta:
        model = ServiceRepair
        fields = [
            'service_repair_id', 'sr_no', 'tools_equipment',
            'equipment_no', 'date_started', 'date_completed'
        ]


class ListServiceRepairDetailSerializer(serializers.ModelSerializer):

    service_repair_id = serializers.UUIDField(source='id')
    equipment_log = ListEquipmentLogSerializer(many=False)
    materials = ListMaterialSerializer(many=True)
    date = serializers.DateField(format='%d-%m-%Y')
    date_started = serializers.DateField(format='%d-%m-%Y')
    date_completed = serializers.DateField(format='%d-%m-%Y')

    class Meta:
        model = ServiceRepair
        fields = [
            'service_repair_id', 'sr_no', 'repair_no', 'date',
            'site', 'tools_equipment', 'serial_equipment_number', 'color',
            'equipment_log', 'materials', 'repaired_by', 'date_started',
            'date_completed', 'remarks', 'requested_by', 'noted_by', 'approved_by'
        ]

class UpdateEquipmentLogsSerializer(serializers.ModelSerializer):

    equipment_log_id = serializers.UUIDField(source='id')

    status = serializers.CharField(
        error_messages={
            "required": "Status is required",
            "blank": "Status must not be blank",
        }
    )
    action_type = serializers.CharField(
        error_messages={
            "blank": "Action type is required",
            "required": "Action type is required"
        }
    )
    action_date = serializers.DateField(
        input_formats=['%d-%m-%Y'],
        error_messages={
            "invalid": f"Invalid date format use this instead: DD-MM-YYYY"
        }
    )
    last_repaired = serializers.DateField(
        input_formats=['%d-%m-%Y'],
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "Invalid last repaired format use this instead: DD-MM-YYYY"
        }
    )
    last_replacement = serializers.DateField(
        input_formats=['%d-%m-%Y'],
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "Invalid last replacement format use this instead: DD-MM-YYYY"
        }
    )
    last_maintenance = serializers.DateField(
        input_formats=['%d-%m-%Y'],
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "Invalid last maintenance format use this instead: DD-MM-YYYY"
        }
    )
    problems_encountered = serializers.CharField(
        allow_blank=True,
        allow_null=True
    )
    works_service_done = serializers.ListField(
        child=serializers.CharField(
            error_messages={
                "required": "Works/Service done is required",
                "blank": "Works/Service done must not be blank"
            }
        )
    )

    class Meta:
        model = EquipmentLog
        fields = [
            'equipment_log_id', 'status', 'transferred_to', 'action_type',
            'action_date', 'last_repaired', 'last_replacement',
            'last_maintenance', 'problems_encountered', 'works_service_done'
        ]

    def validate(self, attrs):

        status = attrs.get('status', None)

        transferred_to = attrs.get('transferred_to', None)

        if status == ServiceChoices.TRANSFERRED and not transferred_to:
            raise_validation("Both transffered to value must be present")

        return attrs
    
class UpdateMaterialSerializer(serializers.ModelSerializer):

    material_id = serializers.UUIDField(source='id')

    items = StrictCharField(
        error_messages={
            "required": "Items is required",
            "blank": "Items must not be blank"
        }
    )

    quantity = serializers.IntegerField(
        error_messages={
            "required": "Quantity is required",
            "blank": "Quantity must not be blank",
            "invalid": "Quantity must be a number",
            "null": "Quantity must not be null"
        }
    )

    class Meta:
        model = Material
        fields = ['material_id', 'items', 'quantity']


    def validate_quantity(self, value):
        if value < 0:
            raise_validation("Quantity must be a positive value")
        return value


class ExistingServiceEquipmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = ServiceRepair
        fields = ['tools_equipment']

class UpdateServiceRepairSerializer(serializers.ModelSerializer):   

    sr_no = StrictCharField(
        required=True,
        allow_blank=False,
        allow_null=False,
        error_messages={
            "required": "Sr no is required",
            "blank": "Sr no cannot must not be blank",
            "null": "Sr no cannot be null"
        }
    )
    repair_no = StrictCharField(
        error_messages={
            "required": "Repair no is required",
            "blank": "Repair no must not be blank",
            "null": "Repair no cannot be null"
        }
    )
    date = serializers.DateField(
        input_formats=['%d-%m-%Y'],
        error_messages={
            "invalid": "Invalid date format use this instead: DD-MM-YYYY"
        }
    )
    site = StrictCharField(
        error_messages={
            "required": "Site is required",
            "blank": "Site must not be blank",
            "null": "Site cannot be null"
        }
    )
    tools_equipment = StrictCharField(
        error_messages={
            "required": "Tools/Equipment is required",
            "blank": "Tools/Equipment must not be blank",
            "null": "Tools/Equipment cannot be null"
        }
    )
    serial_equipment_number = StrictCharField(
        error_messages={
            "required": "Serial/Equipment Number is required",
            "blank": "Serial/Equipment Number must not be blank",
            "null": "Serial/Equipment Number cannot be null"
        }
    )
    color = StrictCharField(
        error_messages={
            "required": "Color is required",
            "blank": "Color must not be blank",
            "null": "Color cannot be null"
        }
    )

    repaired_by = StrictCharField(
        error_messages={
            "required": "Repaired by is required",
            "blank": "Repaired by cannot be blank",
            "null": "Repaired by cannot be blank"
        }
    )

    equipment_log = UpdateEquipmentLogsSerializer(many=False)

    materials = UpdateMaterialSerializer(many=True)

    date_started = serializers.DateField(
        allow_null=True,
        input_formats=['%d-%m-%Y'],
        error_messages={
            "invalid": "invalid date started format use this instead: DD-MM-YYYY",
            "null": "Date started cannot be null"
        }
    )
    date_completed = serializers.DateField(
        allow_null=True,
        input_formats=['%d-%m-%Y'],
        error_messages={
            "invalid": "invalid date completed format use this instead: DD-MM-YYYY",
            "null": "Date completed cannot be null"
        }
    )
    remarks = StrictCharField(
        allow_blank=True,
        allow_null=True,
        required=False,
        error_messages={
            "required": "Remarks is required",
            "blank": "Remarks must not be blank"
        }
    )
    requested_by = StrictCharField(
        error_messages={
            "required": "Requested by is required",
            "blank": "Requested by must not be blank",
            "null": "Requested by cannot be null"
        }
    )
    noted_by = StrictCharField(
        error_messages={
            "required": "Notes by is required",
            "blank": "Notes by must not be blank",
            "null": "Noted by cannot be null"
        }
    )
    approved_by = StrictCharField(
        error_messages={
            "required": "Approved by by is required",
            "blank": "Approved by by must not be blank",
            "null": "Approved by cannot be null"
        }
    )
 

    class Meta:
        model = ServiceRepair
        fields = [
            'sr_no', 'repair_no', 'date', 'site',
            'tools_equipment', 'serial_equipment_number', 'color', 'repaired_by',
            'equipment_log', 'materials', 'date_started', 'date_completed',
            'remarks', 'requested_by', 'noted_by', 'approved_by'
        ]

    def validate(self, attrs):
        return attrs


    def update(self, instance, validated_data):


        # Extract the nested serializers
        materials_data = validated_data.pop('materials', [])
        equipment_log_data = validated_data.pop('equipment_log', None)

        equipments = Equipment.objects.filter(equipment=instance.equipments)

        # for equipment in equipments:
        #     Equipment.objects.filter(id=equipment.id).update(
        #         site=validated_data.get('site'),
        #         color=validated_data.get('color'),
        #         equipment_no=validated_data.get('serial_equipment_number'),
        #         equipment=validated_data.get('tools_equipment'),
        #         problems_encountered=equipment_log_data.get('problems_encountered'),
        #         service_rendered=equipment_log_data.get('works_service_done'),
        #         remarks=validated_data.get('remarks'),
        #         mechanic=validated_data.get('repaired_by')
        #     )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        existing_materials = {m.id: m for m in instance.materials.all()}

        for material_data in materials_data:

            material_id = material_data.get('id', None)

            if material_id and material_id in existing_materials:

                # Update existing material
                material_instance = existing_materials[material_id]

                for attr, value in material_data.items():
                    setattr(material_instance, attr, value)
                material_instance.save()
            else:
                instance.materials.create(**material_data)

            # for equipment in equipments:
            #     Equipment.objects.filter(id=equipment.id).update(
            #         quantity=material_data.get('quantity', 0),
            #         materials_purchased=material_data.get('items', None)
            #     )

  
        if equipment_log_data:
            log_instance = instance.equipment_log

            for attr, value in equipment_log_data.items():
                setattr(log_instance, attr, value)

            log_instance.save()
        
        return instance


# Import service repair

class ImportxlsxInServiceRepairSerializer(serializers.Serializer):

    excel_file = serializers.FileField()

    @staticmethod
    def str_to_bool(val):
        return str(val).strip().upper() == "TRUE"

    def validate(self, attrs):
        file = attrs.get("excel_file")
        if not file.name.endswith('.xlsx'):
            raise serializers.ValidationError("Only Excel files are allowed.")
        return attrs
    
    def parse_date(self, value):
        if not value or value.strip().lower() == "none":
            return None
        return datetime.strptime(value, '%d-%b-%Y').date()

    def create(self, validated_data):

        excel_file = validated_data["excel_file"]

        wb = load_workbook(filename=BytesIO(excel_file.read()), data_only=True)
        sheet = wb.active
        is_seen = defaultdict(list)
        grouped_data = defaultdict(list)
        failed_imports = []
        seen_failures = set()
        created_service_repairs = []


        headers = [cell.value for cell in sheet[1]]

        for rows in sheet.iter_rows(min_row=2, values_only=True):
            row_dict = dict(zip(headers, rows))
            service_repair_equipment = row_dict.get("EQUIPMENT")
            if service_repair_equipment:
                grouped_data[service_repair_equipment].append(row_dict)
        # Process each group
        for _, rows in grouped_data.items():

            items_data = []
            logs_data = []
            materials_data = []

            try:
                for row in rows:
                    
                    service_rendered_raw = row.get('SERVICE RENDERED')
                    if isinstance(service_rendered_raw, str):
                        raw_service_rendered_list = [x.strip() for x in service_rendered_raw.split(",") if x.strip()]
                    else:
                        raw_service_rendered_list = []

                    eq_no = row.get('EQUIPMENT NO.')

                    if eq_no and not ServiceRepair.objects.filter(serial_equipment_number=row.get('EQUIPMENT NO.')).exists():

                        if eq_no not in is_seen:
                            
                            service_repair = ServiceRepair(
                                tools_equipment=str(row.get('EQUIPMENT')).lower(),
                                serial_equipment_number=str(row.get('EQUIPMENT NO.')).upper(),
                                site=str(row.get('SITE')).lower(),
                                color=str(row.get('COLOR')).lower(),
                                date=self.parse_date(row.get('DATE')),
                                sr_no=str(row.get('SR NO')).lower(),
                                repair_no=str(row.get('REPAIR NO')).lower(),
                                repaired_by=str(row.get('REPAIRED BY')),
                                date_started=self.parse_date(row.get('DATE STARTED')),
                                date_completed=self.parse_date(row.get('DATE COMPLETED')),
                                remarks=str(row.get('REMARKS')).lower(),
                                requested_by=str(row.get('REQUESTED BY')),
                                noted_by=str(row.get('NOTED BY')),
                                approved_by=str(row.get('APPROVED BY'))
                            )

                            items_data.append(service_repair)
                        
                            current_service_repair = service_repair

                            equipment_log = EquipmentLog(
                                problems_encountered=str(row.get('PROBLEMS ENCOUNTERED')).lower(),
                                status=str(row.get('STATUS')).lower(),
                                action_type=str(row.get('SERVICE TYPE')),
                                action_date=self.parse_date(row.get('SERVICE DATE')),
                                last_repaired=self.parse_date(row.get('LAST REPAIRED')),
                                last_replacement=self.parse_date(row.get('LAST REPLACEMENT')),
                                last_maintenance=self.parse_date(row.get('LAST MAINTENANCE')),
                                works_service_done=raw_service_rendered_list,
                                service_repair=service_repair
                            )

                            logs_data.append(equipment_log)

                            is_seen[eq_no] = row.get('EQUIPMENT')
                            

                        materials_raw = str(row.get('MATERIALS PURCHASED'))
                        quantities_raw = str(row.get('QUANTITY'))

                        if materials_raw and quantities_raw:
                            material_items = [x.strip() for x in materials_raw.split(",") if x.strip()]
                            material_quantities = [x.strip() for x in quantities_raw.split(",") if x.strip()]

                            for item, qty in zip(material_items, material_quantities):
                                materials = Material(
                                    items=item,
                                    quantity=qty,
                                    service_repair=current_service_repair
                                )
                                materials_data.append(materials)


                    else:
                        if eq_no not in seen_failures:
                            failed_imports.append({
                                "equipment_no": eq_no,
                                "error": "Already exists"
                            })
                            seen_failures.add(eq_no)

                created_items = ServiceRepair.objects.bulk_create(items_data)

                EquipmentLog.objects.bulk_create(logs_data)

                Material.objects.bulk_create(materials_data)

                created_service_repairs.extend(created_items)

                # equipment_map = defaultdict(list)

                # Build equipment map for M2M Linking
                # for equipment in created_items:
                #     key = (equipment.sr_no)
                #     if key:
                #         equipment_map[key].append(equipment.pk)
                
                # # Relink M2M
                # try:
                #     with transaction.atomic():
                #         for sr_key, eq_pks in equipment_map.items():
                #             try:
                #                 service_repair = ServiceRepair.objects.get(sr_no=sr_key)
                #             except ServiceRepair.DoesNotExist:
                #                 continue
                #             # Relink M2M
                #             service_repair.equipments.add(*eq_pks)
                # except Exception as e:
                #     raise_validation(e)

            except Exception as e:
                raise_validation(e)

        if failed_imports:
            raise_validation(failed_imports)
        
        return created_service_repairs
# Import equipment V3



