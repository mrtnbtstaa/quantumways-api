from django.db import models
from quantumways.models import TimestampModel
import uuid

class ServiceChoices:

    FOR_REPAIR = "for repair"
    REPLACEMENT = "replacement"
    FOR_MAINTENANCE = "for maintenance"

    NEW = 'new'
    OLD = 'old'
    TRANSFERRED = 'transferred to'

    STATUS_CHOICES = [
        ('new', 'New'),
        ('old', 'Old'),
        ('transferred to', 'Transferred To')
    ]

    ACTION_CHOICES = [
        (FOR_REPAIR, 'For Repair'),
        (REPLACEMENT, 'Replacement'),
        (FOR_MAINTENANCE, 'For Maintenance'),
    ]

class ServiceRepair(TimestampModel):

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    sr_no = models.CharField(null=True, blank=True)
    repair_no = models.CharField(
        null=False,
        blank=False
    )
    date = models.DateField(
        null=False,
        blank=False
    )
    site = models.CharField(
        null=False,
        blank=False
    )

    equipments = models.ManyToManyField(
        'master_list_app.Equipment',
        related_name='service_repairs',
        blank=True
    )
    # equipment = models.ForeignKey(
    #     'master_list_app.Equipment',
    #     on_delete=models.SET_NULL,
    #     related_name='service_repairs',
    #     null=True
    # )

    tools_equipment = models.CharField(
        null=False,
        blank=False
    )
    serial_equipment_number = models.CharField(
        null=False,
        blank=False
    )
    color = models.CharField(
        null=False,
        blank=False
    )

    repaired_by = models.CharField(
        null=False,
        blank=False
    )
    date_started = models.DateField(
        null=False,
        blank=False
    )
    date_completed = models.DateField(
        null=True,
        blank=True
    )

    remarks = models.CharField(
        null=False,
        blank=False
    )

    requested_by = models.CharField(
        null=False,
        blank=False
    )
    noted_by = models.CharField(
        null=False,
        blank=False
    )
    approved_by = models.CharField(
        null=False,
        blank=False
    )

    def __str__(self):
        return self.sr_no


class Material(TimestampModel):

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    items = models.CharField(
        null=False,
        blank=False
    )
    quantity = models.IntegerField(
        null=False,
        blank=False
    )
    service_repair = models.ForeignKey(to=ServiceRepair, on_delete=models.CASCADE, related_name='materials', null=True)

    def __str__(self):
        return self.items


class EquipmentLog(TimestampModel):

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)

    status = models.CharField(
        max_length=20,
        choices=ServiceChoices.STATUS_CHOICES,
        null=False,
        blank=False
    )
    transferred_to = models.CharField(null=True, blank=True)
    
    action_type = models.CharField(
        max_length=20,
        choices=ServiceChoices.ACTION_CHOICES,
        null=False,
        blank=False
    )
    action_date = models.DateField(
        null=False,
        blank=False
    )
    
    last_repaired = models.DateField(null=True, blank=True)
    
    last_replacement = models.DateField(null=True, blank=True)
    
    last_maintenance = models.DateField(null=True, blank=True)

    problems_encountered = models.TextField(
        max_length=1000,
        null=False,
        blank=False
    )
    works_service_done = models.JSONField(
        default=list,
        null=False,
        blank=False
    )
    # works_service_done = models.CharField(
    #     max_length=1000,
    #     null=False,
    #     blank=False
    # )
    service_repair = models.OneToOneField(to=ServiceRepair, on_delete=models.CASCADE, related_name='equipment_log')

    def __str__(self):
        return self.action_type






