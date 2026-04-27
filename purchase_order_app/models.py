from django.db import models
from quantumways.models import TimestampModel
import uuid

class PurchaseOrder(TimestampModel):

    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    po_control_no = models.CharField(max_length=30, null=True, blank=True)
    document_revisions = models.CharField(max_length=100, null=True)
    pr_no = models.CharField(max_length=30)
    cash_payment = models.BooleanField(default=False, null=True, blank=True)
    cheque_payment = models.BooleanField(default=False, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    po_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Purchase number: {self.pr_no}" if self.po_control_no in (None, "") else f"Purchase control number: {self.po_control_no}"
    
    def save(self, *args, **kwargs):
        # Only save the latest control no if self control no is None
        if self.po_control_no in (None, ""):
            po_control_nos = PurchaseOrder.objects.exclude(po_control_no__isnull=True).values_list("po_control_no", flat=True)
            # Filter only numeric po control numbers
            numeric_po_control_nos = []
            for c in po_control_nos:
                try:
                    if c.startswith("F-"):
                        number_part = c[2:] # Strip 'F-' Prefix
                        if number_part.isdigit():
                            numeric_po_control_nos.append(int(number_part))
                except ValueError:
                    continue
            


            # Determine the next number
            next_po_control_no = max(numeric_po_control_nos, default=0) + 1
            
            # Always prefix with "F-00" + number (F-001, F-0010)
            self.po_control_no = f"F-00{next_po_control_no}"

        super().save(*args, **kwargs)

class PurchaseVendee(TimestampModel):
    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    purchase_order = models.OneToOneField(to=PurchaseOrder, on_delete=models.CASCADE, related_name='vendee')
    company_name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    phone_email = models.CharField(max_length=100)

    def __str__(self):
        return self.company_name

class PurchaseProject(TimestampModel):
    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    purchase_order = models.OneToOneField(to=PurchaseOrder, on_delete=models.CASCADE, related_name='project')
    project_name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    phone_email = models.CharField(max_length=100)

    def __str__(self):
        return self.project_name

class PurchaseAdditionalInformation(TimestampModel):
    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    purchase_order = models.OneToOneField(to=PurchaseOrder, on_delete=models.CASCADE, related_name='additional_information')
    for_delivery = models.BooleanField(default=False, null=True, blank=True)
    for_pick_up_by = models.BooleanField(default=False, null=True, blank=True)
    for_pick_up_by_text = models.CharField(max_length=100, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Purchase number: {self.purchase_order.pr_no}" if self.purchase_order.po_control_no in (None, "") else f"Purchase control number: {self.purchase_order.po_control_no}"

class PurchaseItem(TimestampModel):
    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    purchase_order = models.ForeignKey(to=PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    quantity = models.IntegerField()
    description = models.TextField(max_length=255)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Purchase number: {self.purchase_order.pr_no}" if self.purchase_order.po_control_no in (None, "") else f"Purchase control number: {self.purchase_order.po_control_no}"





