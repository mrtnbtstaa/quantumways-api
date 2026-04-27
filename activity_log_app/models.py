from django.db import models
from quantumways.models import TimestampModel
from authentication_app.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid

class ActivityLog(TimestampModel):

    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    users = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='users')
    date = models.DateTimeField(auto_now_add=True, null=True)
    activity_type = models.CharField(max_length=50, null=True)
    changes = models.CharField(max_length=500, null=True)


    # Generic relation to any model -> (purchaserequest, purchaseorder, and so on)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.UUIDField(null=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    unique_no = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.changes

