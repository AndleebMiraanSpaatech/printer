from .base_serializers import AutoNestedSerializer

def get_auto_serializer(model_class):
    class GenericSerializer(AutoNestedSerializer):
        class Meta:
            model = model_class
            fields = '__all__'
    return GenericSerializer