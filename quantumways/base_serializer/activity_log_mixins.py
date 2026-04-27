from quantumways.create_activity_log import create_activity_log

class ActivityLogMixin:
    """
        Mixin to log activity after create/update/delete
    """
    created_activity_type_message = None
    created_activity_changes_message = None

    update_activity_type_message = None
    update_activity_changes_message = None

    delete_activity_type_message = None
    delete_activity_changes_message = None

    unique_control_no = None

    def log_activity(self, request, instance):
        """
            Only add log if "unique_control_no" is not None
        """
        if not self.unique_control_no:
            return
        
        unique_no = getattr(instance, self.unique_control_no, None) # Get the unique control number

        if not unique_no:
            return

        create_activity_log(
            request=request,
            activity_type=self.created_activity_type_message,
            content_object=instance,
            unique_no=unique_no,
            changes=f"{self.created_activity_changes_message} #{unique_no}"
        )