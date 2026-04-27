from rest_framework import generics, mixins, status
from rest_framework.parsers import MultiPartParser
from quantumways.permissions import HasFeatureAccess
from rest_framework.permissions import IsAuthenticated
from quantumways.utils import response_message_utils, extract_first_error_message, split_ids_and_slugs
from quantumways.export_to_excel import export_to_excel
from django.db.models import Q

class BaseExportView(generics.CreateAPIView):

    feature_name = None # Name of the feature for permission checking (used with custom permissions)
   
    permission_classes = [IsAuthenticated, HasFeatureAccess]  # List of permission classes that control access to this view

    model = None # The model associated with the view (e.g,. PurchaseRequest)

    ids_or_no = None # Key from request data

    unique_no = None # Unique field (e.g., 'pr_no', 'control_no')

    prefetch_related_model = None # e.g., `purchase_items`

    items_attr = None # e.g., `purchase_items`

    file_name = None

    formatters = None 

    title_export = None

    use_values_list = False

    def get_queryset(self, valid_uuids, valid_slugs):
        """
            Must be overridden in subclasses to define export logic.
        """
        raise NotImplementedError("Subclass must implement `get_queryset()`")

    def get_headers(self):
        """
            Must return list of header strings.
        """
        raise NotImplementedError("Subclass must implement `get_headers` method")


    def format_row(self, obj, item):
        """
            Optional override if use_values_list = False
        """
        raise NotImplementedError("Subclass must implement `format_row` method")

    def post(self, request, *args, **kwargs):
        

        try:
            
            ids_or_no = self.request.data.get(self.ids_or_no)
            # Extract and get the uuids or slugs(control no, pr number, voucher id)
            valid_uuids, valid_slugs = split_ids_and_slugs(ids_or_no)

            filter_unique_no = {f"{self.unique_no}__in": valid_slugs}

            if not self.model.objects.filter(
                Q(id__in=valid_uuids) | Q(**filter_unique_no)
            ).exists():
                
                return response_message_utils(
                    message="No ids or no found",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            queryset = self.get_queryset(valid_uuids, valid_slugs)
            headers = self.get_headers()

            rows = []

            if self.use_values_list:
                for row in queryset:
                    if not isinstance(row, (list, tuple)):
                        raise ValueError(f"Expected list/tuple from values_list, got {type(row)}: {row}")
                    rows.append(list(row))
            else:
                for obj in queryset:
                    items = getattr(obj, self.items_attr).all()
                    for item in items:
                        row = self.format_row(obj, item)
                        if not isinstance(row, list):
                            raise ValueError(f"Expected list from format_row, got {type(row)}: {row}")
                        rows.append(row)


            if not isinstance(headers, list):
                return response_message_utils(
                    message="Headers must be a list of strings",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return export_to_excel(
                headers=headers,
                file_name=self.file_name,
                queryset=rows,
                formatters=self.formatters,
                title=self.title_export
            )


        except Exception as e:
            print("[DEBUG] HEADERS TYPE:", type(self.headers))
            print("[DEBUG] HEADERS VALUE:", self.headers)
            return response_message_utils(
                message=f"Something went wrong while exporting your excel {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )