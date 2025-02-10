from rest_framework import serializers

class DataItemSerializer(serializers.Serializer):
    order = serializers.IntegerField()
    value = serializers.CharField(max_length=2)

class CoordinatesSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    phone = serializers.IntegerField()
    data = DataItemSerializer(many=True)

class ResultDataInputSerializer(serializers.Serializer):
    image_url = serializers.URLField()
    coordinates = CoordinatesSerializer()
