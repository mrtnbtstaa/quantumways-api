from django.apps import AppConfig


class PurchaseRequestAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'purchase_request_app'

    # def ready(self):
    #     import purchase_request_app.signals
