from quantumways.utils import response_message_utils
from rest_framework import status
from rest_framework.decorators import action

class BulkDeleteMixin:

    """
        Provides a reusable method for bulk delete and single delete with activity logging
    """
    def destroy(self, request, *args, **kwargs):

        # If pk is provided -> normal delete
        lookup_field = getattr(self, 'lookup_field', 'pk')

        if lookup_field not in kwargs:
            return response_message_utils(
                message="Missing id for delete",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        instance = self.model.objects.filter(id=kwargs.get(lookup_field)).first()
        
        if hasattr(self, 'log_activity'):
            self.log_activity(self.request, instance) # Invoke the activity log

        self.perform_destroy(instance)

        return response_message_utils(
            message=getattr(self, "success_delete_message", "Successfully deleted."),
            status_code=status.HTTP_200_OK
        )
        
        
    @action(detail=False, methods=["delete"], url_path='bulk')
    def bulk_delete(self, request, *args, **kwargs):
        """
        Handles bulk delete
        """
        ids_or_no = request.data.get("ids_or_no", [])

        if not isinstance(ids_or_no, list) or len(ids_or_no) < 1:
            return response_message_utils(
                message="ids_or_no` must be a non-empty list.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        qs = self.model.objects.filter(id__in=ids_or_no)
        deleted_count = qs.count()

        if deleted_count != len(ids_or_no):
            return response_message_utils(
                message=getattr(self, "not_found_message", "One or more items not found."),
                status_code=status.HTTP_404_NOT_FOUND
            )

        for instance in qs:
            if hasattr(self, "log_activity"):
                self.log_activity(request, instance)

        qs.delete()

        return response_message_utils(
            message=getattr(self, "success_bulk_delete_message", "Successfully bulk deleted."),
            status_code=status.HTTP_200_OK
        )