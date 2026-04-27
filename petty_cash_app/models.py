from django.db import models
from quantumways.models import TimestampModel
import uuid

class PettyCash(TimestampModel):

    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    control_no = models.CharField(null=True, blank=True)
    document_revisions = models.CharField(max_length=100, null=True)
    pc_given = models.IntegerField()
    date = models.DateField(null=True, blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    requested_and_received_by = models.CharField(max_length=100, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    released_by = models.CharField(max_length=100, null=True, blank=True)
    remarks = models.CharField(max_length=100, null=True, blank=True)


    def __str__(self):
        return (
            str(self.id)
            if self.control_no in (None, "")
            else self.control_no
        )
    
    def save(self, *args, **kwargs):
        # Only save the latest control no if self control no is None
        if self.control_no in (None, ""):
            control_nos = PettyCash.objects.exclude(control_no__isnull=True).exclude(control_no="").values_list("control_no", flat=True)

            # Filter only numeric control numbers
            numeric_control_nos = []
            for c in control_nos:
                try:
                    numeric_control_nos.append(int(c))
                except ValueError:
                    continue

            # Determine the next number
            next_control_no = max(numeric_control_nos, default=0) + 1
            
            # Format it to always start with "00"
            self.control_no = f"0000{next_control_no}"

        return super().save(*args, **kwargs)
    
class PettyItem(TimestampModel):

    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    petty_cash = models.ForeignKey(to=PettyCash, on_delete=models.CASCADE, related_name='items')
    no_of_items = models.IntegerField()
    unit = models.CharField(null=True, blank=True)
    services_purchased = models.CharField(max_length=100, null=True, blank=True)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return self.services_purchased
