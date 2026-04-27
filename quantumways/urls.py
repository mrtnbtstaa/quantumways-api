from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def ping(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ping/', ping, name='ping'),
    path('api/', include('authentication_app.urls')),
    path('api/', include('purchase_request_app.urls')),
    path('api/', include('purchase_order_app.urls')),
    path('api/', include('petty_cash_app.urls')),
    path('api/', include('delivery_record_app.urls')),
    path('api/', include('master_list_app.urls')),
    path('api/', include('voucher_liquidation_app.urls')),
    path('api/', include('activity_log_app.urls')),
    path('api/', include('record_app.urls')),
    path('api/', include('permission_app.urls')),
    path('api/', include('dashboard_app.urls')),
    path('api/', include('storage_app.urls')),
    path('api/', include('service_repair_app.urls'))
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

