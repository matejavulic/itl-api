from rest_framework import serializers

class NestedPictureSerializer(serializers.Serializer):
    PIC_TYPES_CHOICES = (
        ("png", "1"),
        ("svg", "2"),
        ("jpg", "3"),
        ("pdf", "4")
    )
    extension = serializers.ChoiceField(choices = PIC_TYPES_CHOICES, default = 1)
    generate = serializers.BooleanField(default = False)
    
class NestedEmailSerilizer(serializers.Serializer):
    email = serializers.EmailField(required = True, max_length = 40)
    subject = serializers.CharField(default = "ITL API Report", max_length = 30)
    
class DataSerializer(serializers.Serializer):
    code = serializers.CharField(required = True, max_length = 5000)
    maskTrace = serializers.BooleanField(default = True)
    timestamp = serializers.DateTimeField(required = True)
    emailOpt = NestedEmailSerilizer(required = False)
    pictureOpt = NestedPictureSerializer(required = False)