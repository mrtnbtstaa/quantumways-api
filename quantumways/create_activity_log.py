from typing import Type, Any
from django.db import models
from django.contrib.contenttypes.models import ContentType
from activity_log_app.models import ActivityLog


def create_activity_log(
    request: Any,
    activity_type: str,
    content_object: Any,
    unique_no: str,
    changes: str
):

    content_type = ContentType.objects.get_for_model(content_object.__class__)
    object_id = content_object.id

    return ActivityLog.objects.create(
    users=request.user,
    activity_type=activity_type,
    content_type=content_type,
    object_id=object_id,
    unique_no=unique_no,
    changes=changes
)
    