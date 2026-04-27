from rest_framework import serializers
from purchase_request_app.models import PurchaseRequest, PurchaseItem
from activity_log_app.models import ActivityLog
from datetime import datetime
from master_list_app.models import Equipment

class ListPurchaseRequestSerializer(serializers.ModelSerializer):

    purchase_request_id = serializers.UUIDField(source='id')

    class Meta:

        model = PurchaseRequest
        fields = ['purchase_request_id' ,'pr_no', 'date_requested', 'date_needed']


class ViewPurchaseItemsDetailsSerializer(serializers.ModelSerializer):

    purchase_item_id = serializers.UUIDField(source='id')

    class Meta:
        model = PurchaseItem
        fields = ['purchase_item_id', 'no', 'quantity', 'unit', 'description', 'purpose']

class ViewPurchaseRequestDetailstSerializer(serializers.ModelSerializer):
    
    purchase_request_id = serializers.UUIDField(source='id')
    purchase_items = ViewPurchaseItemsDetailsSerializer(many=True)

    class Meta:
        model = PurchaseRequest
        fields = [
            'purchase_request_id' ,'pr_no', 'document_revisions', 'date_requested',
            'date_needed', 'project_name', 'location',
            'prepared_by', 'requested_signature', 'remarks',
            'approved_by', 'approved_signature', 'date_time',
            'request_status', 'final_remarks', 'purchase_items'
        ]


class ListActivityLogSerializer(serializers.ModelSerializer):

    time_created = serializers.DateTimeField(format='%I:%M %p', source='created_at')

    class Meta:
        model = ActivityLog
        fields = ['changes', 'time_created']


    def to_representation(self, instance):

        data = super().to_representation(instance)

        user = getattr(instance, 'users', None)

        first_name = getattr(user, 'first_name', None)
        last_name = getattr(user, 'last_name', None)

        profile_image = getattr(getattr(user, 'user_profile', None), 'picture', None).url

        data["first_name"] = first_name
        data["last_name"] = last_name
        data["profile_image"] = profile_image

        return data
    
class ListOfUpcomingBirthdaySerializer(serializers.Serializer):

    first_name = serializers.CharField()
    last_name = serializers.CharField()
    birth_date = serializers.DateField(source='user_information.birth_date', format='%B %d, %Y')
    profile_image = serializers.ImageField(source='user_profile.picture')
    age = serializers.SerializerMethodField()


    def get_age(self, obj):

        # Get the current today datetime
        today = datetime.today().date()
        birth_date = getattr(obj.user_information, 'birth_date', None)
        # Calculate the age
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

        return age


class UpcomingMaintenanceSerializerV2(serializers.ModelSerializer):
    last_conduct_of_pm = serializers.DateField(format='%d-%b-%Y')
    next_pm = serializers.DateField(format='%d-%b-%Y')
    class Meta:
        model = Equipment
        fields = ['equipment_no', 'equipment', 'model', 'last_conduct_of_pm', 'next_pm', 'remarks']
    


    


    