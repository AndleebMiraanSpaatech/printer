from rest_framework import serializers
from django.db.models import ForeignKey, ManyToManyField

class AutoNestedSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        model = self.Meta.model

        # Include forward fields, reverse M2M, and auto-created concrete fields like 'id'
        forward_fields = [
            f for f in model._meta.get_fields()
            if not f.auto_created or (f.auto_created and (f.many_to_many or f.concrete))
        ]

        for field in forward_fields:
            value = getattr(instance, field.name, None)

            if isinstance(field, ForeignKey) and value is not None:
                nested_fields = [
                    f.name for f in value._meta.get_fields()
                    if not (f.auto_created and not f.concrete)
                ]
                serializer_class = type(
                    'NestedSerializer',
                    (serializers.ModelSerializer,),
                    {'Meta': type('Meta', (), {'model': value.__class__, 'fields': nested_fields})}
                )
                ret[field.name] = serializer_class(value).data

            elif isinstance(field, ManyToManyField):
                objs = value.all() if value else []
                if objs:
                    nested_fields = [
                        f.name for f in objs[0]._meta.get_fields()
                        if not (f.auto_created and not f.concrete)
                    ]
                    serializer_class = type(
                        'NestedSerializer',
                        (serializers.ModelSerializer,),
                        {'Meta': type('Meta', (), {'model': objs[0].__class__, 'fields': nested_fields})}
                    )
                    ret[field.name] = [serializer_class(obj).data for obj in objs]
                else:
                    ret[field.name] = []

        return ret
