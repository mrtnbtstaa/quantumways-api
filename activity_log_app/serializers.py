from rest_framework import serializers
from .models import ActivityLog

class ViewActivityLogSerializer(serializers.ModelSerializer):

    date = serializers.DateTimeField(format='%m %B %Y, %I:%M %p')

    class Meta:
        model = ActivityLog
        fields = ['id', 'date', 'activity_type', 'changes']

    def to_representation(self, instance):
        data = super().to_representation(instance)

        MODULE_MAP_NAME = {
            "purchase request": "purchase-requests",
            "purchase order": "purchase-orders",
            "petty cash": "petty-cash",
            "delivery record": "delivery-records",
            "voucher liquidation": "vouchers"
        }

        users = getattr(instance, 'users', None)

        user_role = getattr(getattr(users, 'user_role', None), 'role', None)

        data["user_logs"] = {
            "id": users.id,
            "first_name": users.first_name,
            "last_name": users.last_name,
            "role": user_role
        }

        content_type = getattr(instance, 'content_type', None)

        content_name = getattr(content_type, 'name', None)
        MODULE_API_NAME = MODULE_MAP_NAME.get(content_name)



        if not str(instance.changes).startswith("Deleted"):
            detail_url = f"/api/v1/{MODULE_API_NAME}/{getattr(instance, 'object_id', None)}/"
        else:
            detail_url = None

        data["module"] = {
            "id": getattr(instance, 'object_id', None),
            "unique_no": getattr(instance, 'unique_no', None),
            "module_name": content_name,
            "detail_url": detail_url
        }

        return data



