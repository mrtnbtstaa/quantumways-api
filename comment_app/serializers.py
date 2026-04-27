from rest_framework import serializers
from quantumways.utils import is_field_empty, CustomCharField, CustomBooleanField, raise_validation
from authentication_app.models import User
from .models import Comment

class AddCommentSerializer(serializers.ModelSerializer):

    message = CustomCharField(
        blank_message="Message cannot be blank",
        required_message="Message is required"
    )

    class Meta:
        model = Comment
        fields = ['message']


    def validate_message(self, value):
        
        if is_field_empty(value):
            raise_validation("Message cannot be blank")

        return value

    def create(self, validated_data):
        print(validated_data)
        return Comment.objects.create(
            user=self.context["request"].user,
            content_type=self.context["content_type"],
            object_id=self.context["object_id"],
            message=validated_data.get('message'),
        )
    

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id','first_name', 'last_name']


    def to_representation(self, instance):

        request = self.context.get('request')

        data = super().to_representation(instance)

        user_profile = request.build_absolute_uri(getattr(getattr(instance, 'user_profile', None), 'picture', None).url)

        data["profile_image"] = user_profile

        return data

class ListCommentSerializer(serializers.ModelSerializer):

    user = UserSerializer()

    class Meta:
        model = Comment
        fields = ['id', 'message', 'created_at', 'user']


class UpdateCommentSerializer(serializers.ModelSerializer):

    message = CustomCharField(
        blank_message="Message cannot be blank",
        required_message="Message is required"
    )

    class Meta:
        model = Comment
        fields = ['message']


    def validate_message(self, value):
        
        if is_field_empty(value):
            raise_validation("Message cannot be blank")

        return value

    def update(self, instance, validated_data):
        instance.message = validated_data["message"]
        instance.save()
        return instance
        