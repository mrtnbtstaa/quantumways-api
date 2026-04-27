from django.db import models
from quantumways.models import TimestampModel
import uuid
from django.db.models import Max
from cloudinary_storage.storage import MediaCloudinaryStorage

class DeliveryRecord(TimestampModel):
    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    dr_no = models.CharField(max_length=100, null=True, blank=True)
    document_revisions = models.CharField(max_length=100, null=True)
    date = models.DateField(null=True)
    origin_from = models.CharField(max_length=100, null=True)
    delivered_by = models.CharField(max_length=100, null=True)
    delivered_to = models.CharField(max_length=100, null=True)
    received_by = models.CharField(max_length=100, null=True, blank=True)
    approved_by = models.ImageField(upload_to='delivery_record/', storage=MediaCloudinaryStorage(), max_length=1000, null=True, blank=True)
    remarks = models.CharField(max_length=100, null=True)

    def __str__(self):
        return (
            str(self.id)
            if self.dr_no in (None, "")
            else f"DR No: {self.dr_no}"
        )
    
    def save(self, *args, **kwargs):
        # Only save the latest control no if self control no is None
        if self.dr_no in (None, ""):
            dr_nos = DeliveryRecord.objects.exclude(dr_no__isnull=True).exclude(dr_no="").values_list("dr_no", flat=True)

            # Filter only numeric control numbers
            numeric_dr_nos = []
            for c in dr_nos:
                try:
                    numeric_dr_nos.append(int(c))
                except ValueError:
                    continue

            # Determine the next number
            next_dr_no = max(numeric_dr_nos, default=0) + 1
            
            # Format it to always start with "000"
            self.dr_no = f"000{next_dr_no}"

        super().save(*args, **kwargs)



class DeliveryItem(TimestampModel):
    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    delivery_record = models.ForeignKey(to=DeliveryRecord, on_delete=models.CASCADE, related_name='items')
    item_no = models.IntegerField(null=True, blank=True)
    quantity = models.IntegerField(null=True)
    unit = models.CharField(max_length=100, null=True)
    item_description = models.CharField(max_length=100, null=True)

    def __str__(self):
        return (
            str(self.id)
            if self.delivery_record.dr_no in (None, "")
            else f"DR No: {self.delivery_record.dr_no}"
        )

