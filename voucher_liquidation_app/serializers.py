from rest_framework import serializers
from .models import VoucherExpense, VoucherLiquidation
from quantumways.utils import is_field_empty, raise_validation, CustomCharField, CustomIntegerField, CustomDecimalField
from quantumways.services.services import create_bulk_items
from collections import defaultdict
from django.db import transaction
from io import BytesIO
from openpyxl import load_workbook
from decimal import Decimal
from datetime import datetime
from django.db.models import Sum

class AddVoucherExpenseSerializer(serializers.ModelSerializer):

    date = serializers.DateField(
        error_messages={
            "invalid": "Date must use this format: YYYY-MM-DD"
        }
    )
    particulars = CustomCharField(
        blank_message="Particulars cannot be blank",
        required_message="Particulars is required"
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
        model = VoucherExpense
        fields = ['date', 'particulars', 'amount']

    def to_internal_value(self, data):

        if data["date"] in (None, "") or data["date"].strip() == "":
            raise_validation("Date cannot be blank")

        return super().to_internal_value(data)


    def validate(self, attrs):

        if is_field_empty(attrs["particulars"]):
            raise_validation("Particulars cannot be blank")

        if isinstance(attrs["amount"], Decimal):
            if attrs["amount"] is None:
                raise_validation("Amount cannot be blank")

            if attrs["amount"] < 0:
                raise_validation("Amount must be a positive value")

        return attrs
    
class AddVoucherLiquidationSerializer(serializers.ModelSerializer):
    
    voucher_no = CustomCharField(
        None,
        None,
        required=False,
        allow_blank=True,
        allow_null=True
    )
    document_revisions = CustomCharField(
        blank_message="Document revisions cannot be blank",
        required_message="Document revisions is required"
    )
    voucher_date = serializers.DateField(
        format='%m/%d/%Y',
        input_formats=['%m/%d/%Y'],
        error_messages={
            "invalid": "Voucher date must use this format: MM/DD/YYYY"
        }
    )
    voucher_amount = serializers.IntegerField(
        error_messages={
            "blank": "Voucher amount cannot be blank",
            "null": "Voucher amount cannot have null value",
            "invalid": "Invalid voucher amount value"
        }
    )
    prepared_by = CustomCharField(
        blank_message="Prepared by/date cannot be blank",
        required_message="Prepared by/date is required"
    )
    reviewed_and_received_by = CustomCharField(
        blank_message="Reviewed and received by/date cannot be blank",
        required_message="Reviewed and recieved by/date is required"
    )
    total = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        error_messages={
            "blank": "Total cannot be blank",
            "null": "Total cannot have null value",
            "invalid": "Invalid total value",
        }
    )
    net_settlement = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        error_messages={
            "blank": "Net settlement cannot be blank",
            "null": "Net settlement have null value",
            "invalid": "Invalid net settlement value",
        }
    )
    excess_cash_advance = serializers.BooleanField(
        error_messages={
            "invalid": "Invalid excess cash advance value",
            "null": "excess cash advance cannot have null value"
        }
    )
    excess_actual_expense = serializers.BooleanField(
        error_messages={
            "invalid": "Invalid excess actual expense value",
            "null": "excess actual expense cannot have null value"
        }
    )
    excess_actual_expense_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        error_messages={
            "blank": "Excess actual expense amount cannot be blank",
            "null": "Excess actual expense amount cannot have null value",
            "invalid": "Invalid excess actual expense amount value"
        }
    )
    remarks = CustomCharField(
        blank_message="Remarks cannot be blank",
        required_message="Remarks is required"
    )
    expenses = AddVoucherExpenseSerializer(many=True)

   
    class Meta:
        model = VoucherLiquidation
        fields = [
            'voucher_no', 'document_revisions', 'voucher_date',
            'voucher_amount', 'prepared_by', 'reviewed_and_received_by', 'total',
            'net_settlement', 'excess_cash_advance', 'excess_actual_expense',
            'excess_actual_expense_amount', 'remarks', 'expenses'
        ]

    def to_internal_value(self, data):

        if data["voucher_date"] in (None, "") or data["voucher_date"].strip() == "":
            raise_validation("Voucher date cannot be blank")

        return super().to_internal_value(data)

    def validate(self, attrs):

        if VoucherLiquidation.objects.filter(voucher_no=attrs["voucher_no"]).exists():
            raise_validation(f"Voucher no: {attrs["voucher_no"]} already exists")

        if is_field_empty(attrs["document_revisions"]):
            raise_validation("Document revisions cannot be blank")

        if attrs["voucher_amount"] < 0:
            raise_validation("Voucher amount must be a positive value")

        if is_field_empty(attrs["prepared_by"]):
            raise_validation("Prepared by/date cannot be blank")

        if is_field_empty(attrs["reviewed_and_received_by"]):
            raise_validation("Reviewed and received by/date cannot be blank")

        if attrs["total"] < 0:
            raise_validation("Total must be a positive value")
            
        if attrs["net_settlement"] < 0:
            raise_validation("Net settlement must be a positive value")

        if attrs.get('excess_cash_advance', False) is None:
            raise_validation("Excess cash advance cannot be blank")

        if attrs.get('excess_actual_expense', None) is None and attrs.get('excess_actual_expense_amount', None) is None:
           raise_validation("Excess Actual expense/amount cannot be blank") 
        
        if is_field_empty(attrs["remarks"]):
            raise_validation("Remarks cannote be blank")

        return attrs
    
    def create(self, validated_data):
        
        # Extract the nested serializers data
        expenses_data = validated_data.pop('expenses')


        with transaction.atomic():

            try:
                
                # Create the voucher liquidation associated with the voucher expenses
                voucher_liquidation = create_bulk_items(
                    main_model=VoucherLiquidation,
                    child_model=VoucherExpense,
                    main_data=validated_data,
                    children_data=expenses_data,
                    foreign_key_name='voucher_liquidation'
                )

                # total = VoucherExpense.objects.filter(
                #     voucher_liquidation=voucher_liquidation
                # ).aggregate(
                #     total=Coalesce(Sum('amount'), Value(0, output_field=DecimalField()))
                # )['total']

                # voucher_liquidation.total = total
                # voucher_liquidation.save(update_fields=['total'])
                return voucher_liquidation


            except Exception as e:
                raise_validation(f"Something went wrong when creating the data {e}")

class ImportXlsxInVoucherLiquidationSerializer(serializers.Serializer):

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
        created_voucher = []

        headers = [cell.value for cell in sheet[1]]

        # Group by voucher no
        for rows in sheet.iter_rows(min_row=2, values_only=True):
            row_dict = dict(zip(headers, rows))
            voucher_no = row_dict.get("Voucher No")
            if voucher_no:
                grouped_data[voucher_no].append(row_dict)


        # Process each group
        for vr_no, rows in grouped_data.items():
            try:

                first = rows[0]

                voucher_no = (
                    f"000{first["Voucher No"]}"
                    if not first["Voucher No"].startswith('000')
                    else first["Voucher No"]
                )

                if not VoucherLiquidation.objects.filter(voucher_no=voucher_no).exists():

                    voucher_data = {
                        "voucher_no": voucher_no,
                        "document_revisions": first["Document Revisions"],
                        "voucher_date": datetime.strptime(first["Voucher Date"], "%m/%d/%Y").date(),
                        "voucher_amount": first["Voucher Amount"],
                        "prepared_by": first["Prepared By/Date"],
                        "reviewed_and_received_by": first["Reviewed and Received By/Date"],
                        "net_settlement": first["Net Settlement"],
                        "excess_cash_advance": ImportXlsxInVoucherLiquidationSerializer.str_to_bool(first["Excess Cash Advance"]),
                        "excess_actual_expense": ImportXlsxInVoucherLiquidationSerializer.str_to_bool(first["Excess Actual Expense"]),
                        "excess_actual_expense_amount": first["Excess Actual Expense Amount"],
                        "remarks": first["Remarks"]
                    }

                    items_data = [
                        {
                            "date": datetime.strptime(row["Date"], "%Y/%m/%d").date(),
                            "particulars": row['Particulars'],
                            "amount": row['Amount'],
                        }
                        for row in rows
                    ]

                    voucher_liquidation = create_bulk_items(
                        main_model=VoucherLiquidation,
                        child_model=VoucherExpense,
                        main_data=voucher_data,
                        children_data=items_data,
                        foreign_key_name='voucher_liquidation'
                    )

                    total = voucher_liquidation.expenses.aggregate(total=Sum('amount'))['total'] or 0
                    voucher_liquidation.total = total
                    voucher_liquidation.save(update_fields=['total'])

                    created_voucher.append(voucher_liquidation)
                else:
                    continue

            except Exception as e:
                failed_imports.append({
                    "vr_no": vr_no,
                    "error": str(e)
                })

        if failed_imports:
            raise serializers.ValidationError({
                "message": "Some rows failed to import.",
                "failures": failed_imports
            })
        
        return created_voucher


class ViewVoucherLiquidationSerializer(serializers.ModelSerializer):

    voucher_id = serializers.UUIDField(source='id')
    voucher_date = serializers.SerializerMethodField()

    class Meta:
        model = VoucherLiquidation
        fields = ['voucher_id', 'voucher_no', 'voucher_date']


    def get_voucher_date(self, obj):
        date = obj.voucher_date
        if date:
            return f"{date.month}/{date.day}/{date.strftime('%y')}"
        return None
    

class SearchVoucherLiquidationSerializer(serializers.ModelSerializer):

    voucher_id = serializers.UUIDField(source='id')
    voucher_date = serializers.SerializerMethodField()

    class Meta:
        model = VoucherLiquidation
        fields = ['voucher_id', 'voucher_no', 'voucher_date']


    def get_voucher_date(self, obj):
        date = obj.voucher_date
        if date:
            return f"{date.month}/{date.day}/{date.strftime('%y')}"
        return None

class ViewVoucherExpensesDetailsSerializer(serializers.ModelSerializer):

    voucher_expense_id = serializers.UUIDField(source='id')
    amount = CustomDecimalField(max_digits=12, decimal_places=2)
    date = serializers.DateField(format='%Y-%m-%d')

    class Meta:
        model = VoucherExpense
        fields = ['voucher_expense_id', 'date', 'particulars', 'amount']

class ViewVoucherLiquidationDetailsSerializer(serializers.ModelSerializer):
    
    voucher_date = serializers.SerializerMethodField()
    voucher_id = serializers.UUIDField(source='id')
    expenses = ViewVoucherExpensesDetailsSerializer(many=True)

    class Meta:
        model = VoucherLiquidation
        fields = [
            'voucher_id', 'voucher_no', 'document_revisions', 'voucher_date',
            'voucher_amount', 'prepared_by', 'reviewed_and_received_by', 'total',
            'net_settlement', 'excess_cash_advance', 'excess_actual_expense',
            'excess_actual_expense_amount', 'remarks', 'expenses'
        ]

    def get_voucher_date(self, obj):
        date = obj.voucher_date
        if date:
            return f"{date.month}/{date.day}/{date.strftime('%y')}"
        return None


class UpdateVoucherExpensesSerializer(serializers.ModelSerializer):

    voucher_expense_id = CustomCharField(
        blank_message="Voucher expense id cannot be blank",
        required_message="Voucher expense id is required for updating"
    )
    date = serializers.DateField(
        input_formats=['%Y-%m-%d'],
        error_messages={
            "invalid": "Date must use this format: YYYY-MM-DD"
        }
    )
    particulars = CustomCharField(
        blank_message="Particulars cannot be blank",
        required_message="Particulars is required"
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
        model = VoucherExpense
        fields = ['voucher_expense_id', 'date', 'particulars', 'amount']

    def to_internal_value(self, data):

        if data["date"] in (None, "") or data["date"].strip() == "":
            raise_validation("Date cannot be blank")

        return super().to_internal_value(data)


    def validate(self, attrs):

        if is_field_empty(attrs["voucher_expense_id"]):
            raise_validation("Voucher expense ID is required for updating.")

        if is_field_empty(attrs["particulars"]):
            raise_validation("Particulars cannot be blank")

        if attrs["amount"] < 0:
            raise_validation("Amount must be a positive value")

        return attrs
    

class UpdateVoucherLiquidationSerializer(serializers.ModelSerializer):

    document_revisions = CustomCharField(
        blank_message="Document revisions cannot be blank",
        required_message="Document revisions is required"
    )

    voucher_date = serializers.DateField(
        input_formats=['%m/%d/%y'],
        error_messages={
            "invalid": "Voucher Date must use this format: MM/DD/YY"
        }
    )
    voucher_amount = serializers.IntegerField(
        error_messages={
            "blank": "Voucher amount cannot be blank",
            "null": "Voucher amount cannot have null value",
            "invalid": "Invalid voucher amount value"
        }
    )
    prepared_by = CustomCharField(
        blank_message="Prepared by/date cannot be blank",
        required_message="Prepared by/date is required"
    )
    reviewed_and_received_by = CustomCharField(
        blank_message="Reviewed and received by/date cannot be blank",
        required_message="Reviewed and recieved by/date is required"
    )
    total = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        error_messages={
            "blank": "Total cannot be blank",
            "null": "Total cannot have null value",
            "invalid": "Invalid total value",
        }
    )
    net_settlement = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        error_messages={
            "blank": "Net settlement cannot be blank",
            "null": "Net settlement have null value",
            "invalid": "Invalid net settlement value",
        }
    )
    excess_cash_advance = serializers.BooleanField(
        error_messages={
            "invalid": "Invalid excess cash advance value",
            "null": "excess cash advance cannot have null value"
        }
    )
    excess_actual_expense = serializers.BooleanField(
        error_messages={
            "invalid": "Invalid excess actual expense value",
            "null": "excess actual expense cannot have null value"
        }
    )
    excess_actual_expense_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        error_messages={
            "blank": "Excess actual expense amount cannot be blank",
            "null": "Excess actual expense amount cannot have null value",
            "invalid": "Invalid excess actual expense amount value"
        }
    )
    remarks = CustomCharField(
        blank_message="Remarks cannot be blank",
        required_message="Remarks is required"
    )
    expenses = UpdateVoucherExpensesSerializer(many=True)

    class Meta:
        model = VoucherLiquidation
        fields = [
            'voucher_no', 'document_revisions', 'voucher_date',
            'voucher_amount', 'prepared_by', 'reviewed_and_received_by', 'total',
            'net_settlement', 'excess_cash_advance', 'excess_actual_expense',
            'excess_actual_expense_amount', 'remarks', 'expenses'
        ]

    def to_internal_value(self, data):

        if data["voucher_date"] in (None, "") or data["voucher_date"].strip() == "":
            raise_validation("Voucher date cannot be blank")

        return super().to_internal_value(data)

    def validate(self, attrs):

        if is_field_empty(attrs["document_revisions"]):
            raise_validation("Document revisions cannot be blank")

        if attrs["voucher_amount"] < 0:
            raise_validation("Voucher amount must be a positive value")

        if is_field_empty(attrs["prepared_by"]):
            raise_validation("Prepared by/date cannot be blank")

        if is_field_empty(attrs["reviewed_and_received_by"]):
            raise_validation("Reviewed and received by/date cannot be blank")

        if attrs["total"] < 0:
            raise_validation("Total must be a positive value")

        if attrs["net_settlement"] < 0:
            raise_validation("Net settlement must be a positive value")

        if attrs.get('excess_cash_advance', False) is None:
            raise_validation("Excess cash advance cannot be blank")

        if attrs.get('excess_actual_expense', None) is None and attrs.get('excess_actual_expense_amount', None) is None:
           raise_validation("Excess Actual expense/amount cannot be blank") 
        
        if is_field_empty(attrs["remarks"]):
            raise_validation("Remarks cannote be blank")

        return attrs
    
    def update(self, instance, validated_data): 

        # Extract the nested data items
        expenses_data = validated_data.pop('expenses')


        # Updating voucher liquidations
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Convert keys to string for comparison
        existing_items = {str(item.id): item for item in instance.expenses.all()}
        # Update existing delivery items
        for item_data in expenses_data:
            item_id = str(item_data.get("voucher_expense_id"))

            if item_id and item_id in existing_items:
                item_instance = existing_items[item_id]

                for attr, value in item_data.items():
                    setattr(item_instance, attr, value)

                item_instance.save()

        # total = instance.expenses.aggregate(total=Sum('amount'))['total'] or 0
        # instance.total = total
        # instance.save(update_fields=['total'])

        return instance