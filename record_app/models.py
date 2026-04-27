from django.db import models
from quantumways.models import TimestampModel
import uuid
from decimal import Decimal, InvalidOperation

class Record(TimestampModel):

    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    date = models.DateField(null=True)
    amount_site_per_person = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    petty_cash_given = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    amount_refunded = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return str(self.id)


class RecordItem(TimestampModel):

    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    record = models.ForeignKey(to=Record, on_delete=models.CASCADE, related_name='items')
    pr_no = models.IntegerField(null=True, blank=True)
    pcv_no = models.IntegerField(null=True, blank=True)
    dr_no = models.IntegerField(null=True, blank=True)
    vl = models.IntegerField(null=True, blank=True)
    po_no = models.IntegerField(null=True, blank=True)
    project_site = models.CharField(max_length=50, null=True)
    person_in_charge = models.CharField(max_length=50, null=True)
    equipment = models.CharField(max_length=50, null=True, blank=True)
    supplier = models.CharField(max_length=50, null=True, blank=True)
    type_of_receipt = models.CharField(max_length=50, null=True)
    invoice_receipt_no = models.CharField(max_length=50, null=True)
    receipt_issued_to = models.CharField(max_length=50, null=True)
    qty = models.FloatField(null=True)
    unit = models.CharField(max_length=50, null=True, blank=True)
    product_name = models.CharField(max_length=50, null=True, blank=True)
    item_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    item_unit = models.CharField(max_length=50, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supplier_receipt_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.product_name


