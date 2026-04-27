from rest_framework import serializers
from .models import Folder, File
from quantumways.utils import raise_validation
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
import os
import mimetypes
import cloudinary.uploader
import re
import uuid

User = get_user_model()

# ALLOWED MIMETYPES
ALLOWED_MIME_TYPES = [
    # PDF
    "application/pdf",
    # Images
    "image/png",
    "image/jpeg",
    # Word
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    # Excel
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
]




class CreateFolderSerializers(serializers.ModelSerializer):

    folder_name = serializers.CharField(
        error_messages={
            "required": "Folder name is required",
            "blank": "Folder name cannot be blank",
            "null": "Folder name cannot be null"
        }
    )
    folder_id = serializers.UUIDField(required=False, allow_null=True)


    def validate(self, attrs):

        folder_name = attrs["folder_name"]
        folder_id = attrs.get("folder_id", None)  # this represents the parent folder id

        parent = None

        if folder_id:
            try:
                parent = Folder.objects.get(id=folder_id)
            except Folder.DoesNotExist:
                raise_validation("The specified parent folder does not exist.")

        if Folder.objects.filter(folder_name__iexact=folder_name, parent=parent).exists():
            raise_validation(f"This destination already contains a folder named '{folder_name}'")

        return attrs

    class Meta:
        model = Folder
        fields = ['folder_name', 'folder_id']

    def create(self, validated_data):

        user = self.context.get('user')
        parent = None
        try:
            folder_id = validated_data.pop('folder_id', None)
            parent = Folder.objects.get(id=folder_id)
        except:
            pass

        return Folder.objects.create(
            folder_name=validated_data['folder_name'],
            owner=user,
            parent=parent
        )
    

class ListFolderSerializer(serializers.ModelSerializer):

    folder_id = serializers.UUIDField(source='id')

    class Meta:
        model = Folder
        fields = ['folder_id', 'folder_name', 'owner']


    def to_representation(self, instance):

        data = super().to_representation(instance)

        owner = data.pop('owner')

        try:
            user = User.objects.get(id=owner)
        except User.DoesNotExist:
            raise_validation("No user found")

        data["uploaded_by"] = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "profile_image": getattr(getattr(user, 'user_profile', None), 'picture', None).url
        }

        return data
    
class ListFileDetailSerializer(serializers.ModelSerializer):

    file_id = serializers.UUIDField(source='id')
    file_type = serializers.SerializerMethodField()
    file_url = serializers.URLField(source='url')

    def get_file_type(self, obj):
        guessed_ext = mimetypes.guess_extension(getattr(obj, 'mime_type', None))

        return guessed_ext.lstrip(".")

    class Meta:
        model = File
        fields = ['file_id', 'file_name', 'created_at', 'file_type', 'file_size', 'file_url']

    def to_representation(self, instance):

        data = super().to_representation(instance)

        size = data.pop('file_size')

        for unit in ['bytes', 'KB', 'MB']:
            if size < 1024:
                data["file_size"] = f"{size:.2f} {unit}"
            size /= 1024

        return data

class ListFolderDetailSerializer(serializers.ModelSerializer):

    folder_id = serializers.UUIDField(source='id')
    files = ListFileDetailSerializer(many=True)
    sub_folder = serializers.SerializerMethodField()


    def get_sub_folder(self, obj):
        sub_folder = obj.subfolders.all()
        data = ListFolderDetailSerializer(sub_folder, many=True).data

        owner = getattr(obj, 'owner', None)

        try:
            user = User.objects.get(id=owner.id)
        except User.DoesNotExist:
            raise_validation("No user found")

        uploaded_by_data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "profile_image": getattr(getattr(user, 'user_profile', None), 'picture', None).url
        }

        for item in data:
            item["uploaded_by"] = uploaded_by_data
            item.pop('previous', None)
            item.pop('files', None)
            item.pop('sub_folder', None)

        return data

    def to_representation(self, instance):

        data = super().to_representation(instance)

        folder = instance

        previous_folders = []
        current = folder

        while current is not None:

            parent = current.parent

            folder_id = None

            if current is not None:
                folder_id = current.id
            elif parent is not None:
                folder_id = parent.id

            previous_folders.append({
                "folder_name": current.folder_name,
                "folder_id": folder_id
            })

            # Only include if not the current folder itself
            # if (current.folder_name != folder.folder_name):
            current = parent # Move to the next node

        previous_folders.reverse()

        data["previous"] = previous_folders

        owner = data.pop('owner')

        try:
            user = User.objects.get(id=owner)
        except User.DoesNotExist:
            raise_validation("No user found")

        uploaded_by_data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "profile_image": getattr(getattr(user, 'user_profile', None), 'picture', None).url
        }

        files = data.pop('files')

        for file in files:
            file["uploaded_by"] = uploaded_by_data


        data["files"] = files
        data["sub_folder"] = data.pop('sub_folder')

        return data

    class Meta:
        model = Folder
        fields = ['folder_id', 'folder_name', 'sub_folder', 'files', 'owner']




class FileUploadSerializer(serializers.Serializer):

    files = serializers.ListField(
        child=serializers.FileField(
            validators=[
                FileExtensionValidator(
                    allowed_extensions=['jpg', 'png', 'pdf', 'excel', 'docx', 'xlsx'],
                    message="Only JPG, PNG, PDF, EXCEL, DOCX, XLSX files are allowed"
                )
            ]
        ),
        allow_empty=False,
        error_messages={
            "blank": "File cannot be blank",
            "required": "File is required",
            "invalid": "Invalid file format"
        }
    )

    folder_id = serializers.UUIDField(required=False, allow_null=True)

    # paths = serializers.ListField(child=serializers.CharField(), required=False, allow_null=True)

    def get_or_create_folder_from_path(self, relative_path, owner, parent_folder=None):
        
        parts = relative_path.strip('/').split('/')
        folder = parent_folder
        for part in parts:
            if part:
                folder, _ = Folder.objects.get_or_create(
                    folder_name=part,
                    parent=folder,
                    owner=owner
                )
        return folder

    def validate_files(self, files):

        for file_obj in files:
            mime_type = file_obj.content_type

            if file_obj.size > 3 * 1024 * 1024:
                raise_validation("File size exceeds the allowed limit of 3 MB. Please choose a smaller file")

            if mime_type not in ALLOWED_MIME_TYPES:
                raise_validation(f"Unsupported file type: {mime_type}")

        return files
    
    def create(self, validated_data):

        files = validated_data['files']
        folder_id = validated_data["folder_id"]
      
        user = self.context.get('user')

        try:
            parent_folder = Folder.objects.get(id=folder_id)
        except Folder.DoesNotExist:
            parent_folder = None
            

        results = []
        
        for file_obj in files:
            try:
                
                relative_path = getattr(file_obj, 'webkitRelativePath', file_obj.name)
                folder_path = os.path.dirname(relative_path)
                folder_instance = self.get_or_create_folder_from_path(folder_path, owner=user, parent_folder=parent_folder) if folder_path else parent_folder

                mime_type = file_obj.content_type or mimetypes.guess_type(file_obj.name)[0]
                resource_type = "image" if mime_type and mime_type.startswith("image/") else "raw"
                name, ext = os.path.splitext(file_obj.name)
                safe_name = f"{re.sub(r'[^A-Za-z0-9_\-]', '_', name)}_{uuid.uuid4()}"
                file_format = None

                # Reset file pointer
                if hasattr(file_obj, 'seek'):
                    file_obj.seek(0)

                if ext.lower() == ".pdf":
                    file_format = ext.lstrip('.').lower()

                # Include extension in public_id for raw files
                public_id = f"{safe_name}{ext}" if file_format else safe_name
                # public_id = f"{folder_path.replace(os.sep, '_')}_{safe_name}{ext}" if folder_path else f"{safe_name}{ext}"

                print(f"PUBLIC ID: {public_id}")

                cloudinary_folder = f"files/{folder_path.replace(os.sep, '/')}" if folder_path else "files"
                # Upload to cloudinary
                upload_result = cloudinary.uploader.upload(
                    file_obj,
                    folder=cloudinary_folder,
                    resource_type=resource_type,
                    type="upload",
                    public_id=public_id,
                    unique_filename=True
                )
                

                instance = File.objects.create(
                    file_name=file_obj.name,
                    public_id=upload_result["public_id"],
                    resource_type=upload_result["resource_type"],
                    version=upload_result["version"],
                    file_format=file_format,
                    url=upload_result["secure_url"],
                    folder=folder_instance,
                    owner=user,
                    file_size=file_obj.size,
                    mime_type=file_obj.content_type
                )
                results.append(instance)
            except Exception as e:
                print("EXCEPTION: ",e)
                results.append({"name": file_obj.name, "error": str(e), "status": "failed"})

        return results


class ListFileDetailSerializer(serializers.ModelSerializer):
    
    file_type = serializers.SerializerMethodField()
    file_url = serializers.URLField(source='url')
    file_id = serializers.UUIDField(source='id')

    def get_uploaded_by(self, obj):
        owner = getattr(obj, 'owner', None)
        return f"{getattr(owner, 'first_name', None)} {getattr(owner, 'last_name', None)}"
    
    def get_file_type(self, obj):

        guessed_ext = mimetypes.guess_extension(getattr(obj, 'mime_type', None))

        return guessed_ext.lstrip(".")
    
    def to_representation(self, instance):

        data = super().to_representation(instance)

        size = data.pop('file_size')

        for unit in ['bytes', 'KB', 'MB']:
            if size < 1024:
                data["file_size"] = f"{size:.2f} {unit}"
            size /= 1024

        user_owner = User.objects.get(id=instance.owner.id)

        data["uploaded_by"] = {
            "first_name": user_owner.first_name,
            "last_name": user_owner.last_name,
            "profile_image": getattr(getattr(user_owner, 'user_profile', None), 'picture', None).url
        }

        return data

    class Meta:
        model = File
        fields = ['file_id' ,'file_name', 'file_url', 'file_type', 'file_size', 'created_at']

    

class ZipDownloadFileSerializer(serializers.Serializer):

    ids = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False
    )
    zip_name = serializers.CharField(required=False, default="files")