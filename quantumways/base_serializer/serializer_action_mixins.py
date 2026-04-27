
class SerializerActionByMixin:
    """
        Allows mapping serializers per action (create, list, retrieve, update, etc.)
    """
    serializer_action_classes = {}

    def get_serializer_class(self):
        
        # Try to match the action
        if self.action in self.serializer_action_classes:
           return self.serializer_action_classes[self.action]
        
        return super().get_serializer_class()