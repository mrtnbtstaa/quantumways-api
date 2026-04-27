from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from quantumways.models import TimestampModel
import uuid
from authentication_app.models import User

class Comment(TimestampModel):

    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='comment')

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.UUIDField(null=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    message = models.CharField(max_length=500, null=True)

    def __str__(self):

        return f"{self.user.email} | {self.message}"
