from django.db import models
from quantumways.models import TimestampModel
import uuid
from django.db.models import Max

class Supplier(TimestampModel):
    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    no = models.IntegerField(blank=True, null=True, unique=True)
    item = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.item
    
    def save(self, *args, **kwargs):

        if self.no in(None, ""):
            nos = Supplier.objects.exclude(no__isnull=True).values_list('no', flat=True)

            list_no = []

            for no in nos:
                list_no.append(no)

            next_no = max(list_no, default=0) + 1

            self.no = int(next_no)

        return super().save(*args, **kwargs)
    
class Product(TimestampModel):
    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    no = models.IntegerField(blank=True, null=True, unique=True)
    item = models.CharField(max_length=255, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    unit = models.CharField(max_length=20, null=True)

    def __str__(self):
        return self.item
    
    def save(self, *args, **kwargs):

        if self.no in(None, ""):
            nos = Product.objects.exclude(no__isnull=True).values_list('no', flat=True)

            list_no = []

            for no in nos:
                list_no.append(no)

            next_no = max(list_no, default=0) + 1

            self.no = next_no

        return super().save(*args, **kwargs)


class EquipmentStatus:

    ACTIVE = 'active'
    ONGOING_REPAIR = 'ongoing repair'
    UNDER_MAINTENANCE = "under maintenance"
    OBSOLETE = "obsolete"

    EQUIPMENT_STATUS = [
        (ACTIVE, 'Active'),
        (ONGOING_REPAIR, 'Ongoing Repair'),
        (UNDER_MAINTENANCE, 'Under Maintenance'),
        (OBSOLETE, 'Obsolete')
    ]

    AVAILABLE_STATUS_CHOICES = [ACTIVE, ONGOING_REPAIR, UNDER_MAINTENANCE, OBSOLETE]


class Equipment(TimestampModel):

    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    no = models.IntegerField(blank=True, null=True, unique=True)
    equipment_name = models.CharField(max_length=100, null=True, blank=True)
    equipment_no = models.CharField(max_length=100, null=True)
    model_name = models.CharField(max_length=100, null=True, blank=True)
    last_conduct_of_pm = models.DateField(null=True, blank=True)
    next_pm = models.DateField(null=True, blank=True)
    remarks = models.CharField(max_length=50, null=True)

    # V2 Fields
    equipment = models.CharField(null=True, blank=True)
    brand_name = models.CharField(null=True, blank=True)
    status = models.CharField(choices=EquipmentStatus.EQUIPMENT_STATUS, null=True, blank=True)
    plate_no = models.CharField(null=True, blank=True)
    site = models.CharField(null=True, blank=True)
    color = models.CharField(null=True, blank=True)
    chasis_no = models.CharField(null=True, blank=True)
    model = models.CharField(null=True, blank=True)
    last_inspection = models.DateField(null=True, blank=True)
    last_registration = models.DateField(null=True, blank=True)
    next_registration = models.DateField(null=True, blank=True)
    service_rendered = models.JSONField(default=list, blank=True)
    # service_rendered = models.CharField(null=True, blank=True)
    problems_encountered = models.JSONField(default=list, blank=True)
    # problems_encountered = models.CharField(null=True, blank=True)
    materials_purchased = models.CharField(null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True)
    mechanic = models.CharField(null=True, blank=True)
    is_created_equipment = models.BooleanField(null=True, blank=True)
    sr_no = models.CharField(null=True, blank=True)

    def __str__(self):
        return self.equipment
    
class EquipmentSnapshot(TimestampModel):

    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    equipment = models.CharField(null=True, blank=True)
    service_rendered = models.JSONField(default=list, blank=True)
    problems_encountered = models.JSONField(default=list, blank=True)
    materials_purchased = models.CharField(null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True)
    mechanic = models.CharField(null=True, blank=True)
    remarks = models.CharField(max_length=50, null=True)
    sr_no = models.CharField(null=True, blank=True)
    equipment_no = models.CharField(null=True, blank=True)
    is_created_equipment = models.BooleanField(null=True, blank=True)
    snapshot_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.equipment
    

    


