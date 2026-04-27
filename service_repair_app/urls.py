from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ServiceRepairViews,
    ExistingServiceEquipmentViews,
    ServiceRepairExportView,
    ServiceREpairImportView
)

router = DefaultRouter()

router.register(r'v1/service-repairs', ServiceRepairViews, basename='service-repair')

urlpatterns = [

    path('v1/service-repairs/equipments/', ExistingServiceEquipmentViews.as_view(), name="existing_service_repair_equipments"),
    path('v1/service-repairs/export/', ServiceRepairExportView.as_view(), name='service_repair_export'),
    path('v1/service-repairs/import/', ServiceREpairImportView.as_view(), name='service_repair_import'),

    path('', include(router.urls))
]