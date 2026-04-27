from django.db import models
from quantumways.models import TimestampModel
import uuid

class VoucherLiquidation(TimestampModel):

    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    voucher_no = models.CharField(max_length=30, null=True, blank=True)
    document_revisions = models.CharField(max_length=100, null=True)
    voucher_date = models.DateField(null=True)
    voucher_amount = models.IntegerField(null=True)
    prepared_by = models.CharField(max_length=50, null=True)
    reviewed_and_received_by = models.CharField(max_length=50, null=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    net_settlement = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    excess_cash_advance = models.BooleanField(default=False, null=True, blank=True)
    excess_actual_expense = models.BooleanField(default=False, null=True, blank=True)
    excess_actual_expense_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    remarks = models.CharField(max_length=50, null=True)

    def __str__(self):
        return (
            str(self.id)
            if self.voucher_no in (None, "")
            else self.voucher_no
        )

    def save(self, *args, **kwargs):
        # Only save the latest control no if self control no is None
        if self.voucher_no in (None, ""):
            voucher_nos = VoucherLiquidation.objects.exclude(voucher_no__isnull=True).exclude(voucher_no="").values_list("voucher_no", flat=True)

            # Filter only numeric control numbers
            numeric_voucher_nos = []
            for c in voucher_nos:
                try:
                    numeric_voucher_nos.append(int(c))
                except ValueError:
                    continue

            # Determine the next number
            next_voucher_no = max(numeric_voucher_nos, default=0) + 1
            
            # Format it to always start with "00"
            self.voucher_no = f"000{next_voucher_no}"

        super().save(*args, **kwargs)


class VoucherExpense(TimestampModel):

    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    voucher_liquidation = models.ForeignKey(to=VoucherLiquidation, on_delete=models.CASCADE, related_name='expenses')
    date = models.DateField(null=True)
    particulars = models.CharField(max_length=50, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return (
            str(self.id)
            if self.voucher_liquidation.voucher_no in (None, "")
            else self.voucher_liquidation.voucher_no
        )