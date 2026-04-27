from django.apps import AppConfig


class PurchaseOrderAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'purchase_order_app'


    def ready(self):
        import purchase_order_app.signals