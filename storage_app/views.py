from .models import File, Folder
from quantumways.base_feature_view import BaseFeatureView
from quantumways.base_serializer.base_feature_view_set import BaseFeatureViewSet
from django.http import StreamingHttpResponse
from rest_framework import generics, status
import datetime
from cloudinary import CloudinaryImage
from quantumways.utils import response_message_utils
import io, zipfile, os
from django.db.models import Q
import requests as req
from .serializers import (
    CreateFolderSerializers,
    ListFolderSerializer,
    ListFolderDetailSerializer,
    FileUploadSerializer,
    ListFileDetailSerializer
)

class FoldersView(BaseFeatureViewSet):

    model = Folder

    serializer_action_classes = {
        "create": CreateFolderSerializers,
        "list": ListFolderSerializer,
        "retrieve": ListFolderDetailSerializer,
        "update": None,
        "partial_update": None
    }

    success_create_message = "Successfully created folder"
    success_list_message = "List of folders"
    success_single_delete_message = "Successfully delete the folder"
    not_found_message = "No folder id found"
    success_detail_message = "Successfully found folder"
    success_bulk_delete_message = "Successfully deleted the folders"
    not_found_search = "No file found"
    
    item_to_search = ["folder_name", "files__file_name"]

    def get_queryset(self):
        qs = self.base_get_queryset()

        # Apply select_related (FK/OneToOne) if set
        if self.select_related_model:
            qs = qs.select_related(*self.select_related_model)

        # Apply prefetch_related (M2M/Reverse FK) if set
        if self.prefetch_related_model:
            qs = qs.prefetch_related(*self.prefetch_related_model)

        search = self.request.query_params.get('search')

        if search:
            # Search across all folders/files, regardless of parent
            query = Q()
            for field in self.item_to_search:
                query |= Q(**{f"{field}__icontains": search})
            return qs.filter(query).order_by('created_at')
        else:
            # Only list top-level (parent is null)
            return qs.filter(parent__isnull=True).order_by('created_at')

    def retrieve(self, request, *args, **kwargs):
        
        instance = Folder.objects.filter(id=kwargs.get("id")).first()
        serializer = self.get_serializer(instance)

        return response_message_utils(
            message=self.success_detail_message,
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
    
    def list(self, request, *args, **kwargs):

        queryset = self.filter_queryset(self.get_queryset())

        # Handle pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_data = self.get_paginated_response(serializer.data).data
            return response_message_utils(
                message=self.success_list_message,
                data=paginated_data,
                status_code=status.HTTP_200_OK
            )

        # If no pagination
        serializer = self.get_serializer(queryset, many=True)
        return response_message_utils(
            message=self.success_list_message,
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )


class FileViewSet(BaseFeatureViewSet):

    model = File

    serializer_action_classes = {
        "create": FileUploadSerializer,
        "list": ListFileDetailSerializer,
        "retrieve": ListFileDetailSerializer,
        "update": None,
        "partial_update": None
    }

    item_to_search = ["file_name"]

    success_create_message = "Successfully created file"
    success_delete_message = "Successfully delete the file"
    success_update_message = "Successfully update the file"
    success_detail_message = "Successfully found file"
    success_list_message = "List of file"
    not_found_message = "No file id found"
    not_found_search = "No file found"

    def retrieve(self, request, *args, **kwargs):
        
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return response_message_utils(
            message=self.success_detail_message,
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
    
    def list(self, request, *args, **kwargs):

        queryset = self.filter_queryset(self.get_queryset())

        # Handle pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_data = self.get_paginated_response(serializer.data).data
            return response_message_utils(
                message=self.success_list_message,
                data=paginated_data,
                status_code=status.HTTP_200_OK
            )

        # If no pagination
        serializer = self.get_serializer(queryset, many=True)
        return response_message_utils(
            message=self.success_list_message,
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

class FileView(BaseFeatureView):

    model = File

    lookup_no_field = "id"
  
    create_serializer_class = FileUploadSerializer
    list_serializer_class = ListFileDetailSerializer
    detail_serializer_class = ListFileDetailSerializer

    success_create_message = "Successfully created file"
    success_list_message = "List of files"
    success_single_delete_message = "Successfully delete the file"
    not_found_message = "No file id found"
    success_detail_message = "Successfully found file"
    success_bulk_delete_message = "Successfully deleted the files"



class FileZipDownloadView(generics.CreateAPIView):
    def post(self, request, *args, **kwargs):
        try:
            ids = request.data.get('ids', [])
            if not ids:
                return response_message_utils(
                    message="No file ids provided",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            files = File.objects.filter(id__in=ids)
            if not files:
                return response_message_utils(
                    message="No files found for provided IDs",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            def zip_generator():
                with io.BytesIO() as buffer:
                    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                        for file in files:

                            file_url = CloudinaryImage(file.public_id).build_url(
                                resource_type=file.resource_type,
                                version=file.version,
                                secure=True,
                                sign_url=True
                            )

                            r = req.get(file_url, stream=True)

                            if r.status_code == 200:
                                name = os.path.basename(file.file_name)
                                with zf.open(name, 'w') as dest:
                                    for chunk in r.iter_content(1024 * 1024): # 1MB per chunk
                                        if chunk:
                                            dest.write(chunk)


                    buffer.seek(0)
                    yield from buffer

            filename = f"files_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            response = StreamingHttpResponse(
                zip_generator(),
                content_type='application/zip'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        except Exception as e:
            return response_message_utils(
                message=f"Error processing request: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    