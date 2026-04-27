from django.db import models
from quantumways.models import TimestampModel
import uuid
from django.contrib.auth import get_user_model

User = get_user_model()

class Folder(TimestampModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    folder_name = models.CharField(max_length=255)
    owner = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='folders')
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='subfolders',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.folder_name


class File(TimestampModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_name = models.CharField(max_length=255)
    public_id = models.CharField(max_length=255, unique=True, null=True)
    resource_type = models.CharField(max_length=500, null=True)
    version = models.CharField(max_length=20, null=True)
    file_format = models.CharField(max_length=20, null=True)
    url = models.URLField(max_length=500, null=True)
    folder = models.ForeignKey(
        Folder,
        null=True,
        blank=True,
        related_name='files',
        on_delete=models.CASCADE
    )
    owner = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='files')
    file_size = models.BigIntegerField()
    mime_type = models.CharField(max_length=100, null=True)

    class Meta:
        unique_together = ("public_id", "folder")

    def __str__(self):
        return self.file_name
    
