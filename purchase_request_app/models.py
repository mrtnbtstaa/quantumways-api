from django.db import models
from quantumways.models import TimestampModel
import uuid
from cloudinary_storage.storage import MediaCloudinaryStorage
from quantumways.constants import RequestStatus
from django.db.models import Max

class PurchaseRequest(TimestampModel):

    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    pr_no = models.CharField(max_length=30, blank=True, null=True)
    document_revisions = models.CharField(max_length=100, null=True)
    date_requested = models.DateField(null=True, blank=True)
    date_needed = models.DateField(null=True, blank=True)
    project_name = models.CharField(max_length=100, null=True)
    location = models.CharField(max_length=255, null=True)

    prepared_by = models.CharField(max_length=100)
    requested_signature = models.ImageField(storage=MediaCloudinaryStorage(), upload_to='signatures/', max_length=500, blank=True, null=True)
    remarks = models.CharField(blank=True, null=True)
    approved_by = models.CharField(max_length=100)
    approved_signature = models.ImageField(storage=MediaCloudinaryStorage(), upload_to='signatures/', blank=True, null=True)
    date_time = models.DateTimeField(null=True)

    request_status = models.CharField(choices=RequestStatus.CHOICES, null=True)

    final_remarks = models.CharField(null=True)

    def __str__(self):
        return f"{self.pr_no or self.id}"
    
    def save(self, *args, **kwargs):
        # Only save the latest control no if self control no is None
        if self.pr_no in (None, ""):
            pr_nos = PurchaseRequest.objects.exclude(pr_no__isnull=True).exclude(pr_no="").values_list("pr_no", flat=True)

            # Filter only numeric control numbers
            numeric_pr_nos = []
            for c in pr_nos:
                try:
                    numeric_pr_nos.append(int(c))
                except ValueError:
                    continue

            # Determine the next number
            next_pr_no = max(numeric_pr_nos, default=0) + 1
            
            # Format it to always start with "00"
            self.pr_no = f"00{next_pr_no}"

        super().save(*args, **kwargs)

class PurchaseItem(models.Model):

    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='purchase_items')
    no = models.IntegerField(null=True, blank=True)
    quantity = models.IntegerField()
    unit = models.CharField(max_length=50)
    description = models.CharField(max_length=100, null=True)
    purpose = models.CharField(max_length=100, null=True)
    
    def __str__(self):
        return f"{self.description} ({self.quantity} {self.unit})"
