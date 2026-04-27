from rest_framework import serializers
from .models import Feature, UserFeaturePermission
from quantumways.utils import CustomCharField
from quantumways.utils import is_field_empty, raise_validation
from quantumways.constants import Features

class UserFeaturePermissionSerializer(serializers.ModelSerializer):

    feature_name = CustomCharField(
        blank_message="Feature name cannot be blank",
        required_message="Feature name is required",
        write_only=True
    )

    can_view = serializers.BooleanField(
        error_messages={
            "blank": "Can view cannot be blank",
            "null": "Can view cannot be null",
            "invalid": "Invalid can view value"
        }
    )
    can_add = serializers.BooleanField(
        error_messages={
            "blank": "Can add cannot be blank",
            "null": "Can add cannot be null",
            "invalid": "Invalid can add value"
        }
    )
    can_update = serializers.BooleanField(
        error_messages={
            "blank": "Can update cannot be blank",
            "null": "Can update cannot be null",
            "invalid": "Invalid can update value"
        }
    )
    can_delete = serializers.BooleanField(
        error_messages={
            "blank": "Can delete cannot be blank",
            "null": "Can delete cannot be null",
            "invalid": "Invalid can delete value"
        }
    )

    def validate(self, attrs):
        
        if is_field_empty(attrs["feature_name"]):
            raise_validation("Feature name cannot be blank")

        AVAILABLE_FEATURES = [Features.PURCHASE_REQUEST, Features.PURCHASE_ORDER, Features.DELIVERY_RECORD, Features.PETTY_CASH, Features.VOUCHER_LIQUIDATION]

        if attrs["feature_name"] not in AVAILABLE_FEATURES:
            raise_validation("Invalid feature name")

        if attrs.get('can_view', None) is None:
            raise_validation("Can view cannot be blank")
        if attrs.get('can_add', None) is None:
            raise_validation("Can add cannot be blank")
        if attrs.get('can_update', None) is None:
            raise_validation("Can update cannot be blank")
        if attrs.get('can_delete', None) is None:
            raise_validation("Can delete cannot be blank")

        return attrs

    class Meta:
        model = UserFeaturePermission
        fields = [
            'feature_name',
            'can_view',
            'can_add',
            'can_update',
            'can_delete',
        ]


class AssignUserFeaturePermissionsSerializer(serializers.Serializer):
    
    permissions = UserFeaturePermissionSerializer(many=True)

    def create(self, validated_data):
        
        user = self.context.get('user', None)

        if is_field_empty(user):
            raise_validation("User is required to assign permissions.")

        created_permissions = []

        current_feature_names = []

        permissions_data = validated_data.get('permissions', [])

        for perm in permissions_data:

            feature_name = perm.pop('feature_name')

            current_feature_names.append(feature_name.lower())
            # Get or create the feature record
            feature, _ = Feature.objects.get_or_create(feature_name=feature_name)

            # Update or create user-feature permission
            permission, _ = UserFeaturePermission.objects.update_or_create(
                user=user,
                feature=feature,
                defaults=perm
            )
            created_permissions.append(permission)

        # Delete the old permissions
        UserFeaturePermission.objects.select_related('user_permissions').filter(
            user=user,
        ).exclude(
            feature__feature_name__in=current_feature_names
        ).delete()

        return created_permissions
    

class AssignedPermissionDetailsSerializer(serializers.ModelSerializer):


    class Meta:
        model = UserFeaturePermission
        fields = ['id']


    def to_representation(self, instance):

        data = super().to_representation(instance)

        feature_name = getattr(getattr(instance, 'feature', None), 'feature_name', None)

        data["feature_name"] = feature_name

        return data

    