from django.urls import path, include
from .views import FoldersView, FileView, FileViewSet, FileZipDownloadView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'v1/files', FileViewSet, basename='file')
router.register(r'v1/folders', FoldersView, basename='folder')
urlpatterns = [

    path('v1/files/download-zip/', FileZipDownloadView.as_view(), name='download_zip'),
    
    # path('v1/folders/<str:slug>/', FoldersView.as_view(), name='delete_details_folder'),
    # path('v1/folders/', FoldersView.as_view(), name='list_create_folder'),

    path('', include(router.urls)),
    # path('v1/files/<str:slug>/', FileView.as_view(), name='delete_files'),
    # path('v1/files/', FileView.as_view(), name='list_create_files'),
]