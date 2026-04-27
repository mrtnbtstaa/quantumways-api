from django.db import models
from authentication_app.models import User
from quantumways.models import TimestampModel
import uuid

# Global features like "Petty Cash", "Purchase Request"
class Feature(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feature_name = models.CharField(max_length=50, null=True)

    def __str__(self):
        return self.feature_name


# Per-user permission assignment to a feature
class UserFeaturePermission(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feature_permissions', null=True)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name='user_permissions')

    can_view = models.BooleanField(default=True)
    can_add = models.BooleanField(default=True)
    can_update = models.BooleanField(default=True)
    can_delete = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'feature')

    def __str__(self):
        return f"{self.user.email} | {self.feature.feature_name}"

