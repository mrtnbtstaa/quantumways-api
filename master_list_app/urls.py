from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (

    MasterListSupplierView,
    MasterListSuppliersImportView,
    MasterListSuppliersExportView,

    MasterListProductView,
    MasterListProductsImportView,
    MasterListProductsExportView,

    MasterListEquipmentView,
    MasterListEquipmentImportView,
    MasterListEquipmentExportView,

    ViewExistingSupplierMasterList,
    ViewExistingProductMasterList,
    

    # ------- V2 ------------
    MasterListEquipmentV2ImportView,
    MasterListEquipmentV2ExportView,
    MasterListEquipmentDetailsV2Views,
    MasterListEquipmentV2Views,
    # ------- V2 ------------

    MasterListExistingToolsEquipmentViews,
    MasterListExistingEquipmentNumberViews,

    EquipmentLookupViews,

    # ------- V3 ------------
    MasterListEquipmentV3ExportView,
    MasterListEquipmentV3ImportView
    # ------- V3 ------------
)

router = DefaultRouter()

router.register(r'v2/equipments', MasterListEquipmentV2Views, basename='equipment')

urlpatterns = [

    # Import/Export Actions
    path('v1/suppliers/import/', MasterListSuppliersImportView.as_view(), name='suppliers_import'),
    path('v1/suppliers/export/', MasterListSuppliersExportView.as_view(), name='suppliers_export'),

    # Standard Crud for Suppliers
    path('v1/suppliers/existings/', ViewExistingSupplierMasterList.as_view(), name='existing_suppliers'),
    path('v1/suppliers/', MasterListSupplierView.as_view(), name='create_list_suppliers'),
    path('v1/suppliers/<str:slug>/', MasterListSupplierView.as_view(), name='suppliers_details'),

    # Import/Export Actions
    path('v1/products/import/', MasterListProductsImportView.as_view(), name='products_import'),
    path('v1/products/export/', MasterListProductsExportView.as_view(), name='products_export'),

    # Standard Crud for Products
    path('v1/products/existings/', ViewExistingProductMasterList.as_view(), name='existing_products'),
    path('v1/products/', MasterListProductView.as_view(), name='create_list_products'),
    path('v1/products/<str:slug>/', MasterListProductView.as_view(), name='products_details'),

    # Import/Export Actions
    path('v1/equipments/import/', MasterListEquipmentImportView.as_view(), name='equipments_import'),
    path('v1/equipments/export/', MasterListEquipmentExportView.as_view(), name='equipments_export'),

    # Standard Crud for Equipments
    path('v1/equipments/', MasterListEquipmentView.as_view(), name='create_list_equipments'),
    path('v1/equipments/<str:slug>/', MasterListEquipmentView.as_view(), name='equipments_details'),
    
    path('v2/equipments/import/', MasterListEquipmentV2ImportView.as_view(), name='equipments_v2_import'),
    path('v2/equipments/export/', MasterListEquipmentV2ExportView.as_view(), name='equipments_v2_export'),

    path('v2/equipments/tools/', MasterListExistingToolsEquipmentViews.as_view(), name='existing_equipments'),
    path('v2/equipments/serial-numbers/', MasterListExistingEquipmentNumberViews.as_view(), name='existing_serial_equipment_no'),

    path('v2/equipments/details/<uuid:id>/', MasterListEquipmentDetailsV2Views.as_view(), name='equipment_group_details'),
    path('v2/equipments/lookup/<str:equipment_no>/', EquipmentLookupViews.as_view(), name='equipment_lookup'),
    path('', include(router.urls)),


    path('v3/equipments/import/', MasterListEquipmentV3ImportView.as_view(), name='equipments_v3_import'),
    path('v3/equipments/export/', MasterListEquipmentV3ExportView.as_view(), name='equipments_v3_export'),

]