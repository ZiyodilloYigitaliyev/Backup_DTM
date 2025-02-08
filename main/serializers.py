from rest_framework import serializers
from .models import ImageData, Coordinate

class CoordinateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coordinate
        fields = ["x", "y"]

class ImageDataSerializer(serializers.ModelSerializer):
    coordinates = CoordinateSerializer(many=True)

    class Meta:
        model = ImageData
        fields = ["image_url", "coordinates"]

    def create(self, validated_data):
        coordinates_data = validated_data.pop("coordinates", [])
        
        # Eski image_url va koordinatalarni o‘chirib tashlaymiz
        ImageData.objects.all().delete()

        # Yangi image_url qo‘shamiz
        image_instance = ImageData.objects.create(**validated_data)

        # Koordinatalarni qo‘shamiz
        for coord in coordinates_data:
            Coordinate.objects.create(image=image_instance, **coord)

        return image_instance
    
from rest_framework import serializers
from .models import result  # Model nomingiz "result" deb qabul qilamiz

class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = result
        fields = '__all__'
