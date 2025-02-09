from rest_framework import serializers, views, status
from rest_framework.response import Response
from .models import ProcessedData
from Backup.models import Mapping_Data

class MappingDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mapping_Data
        fields = ('id', 'list_id', 'category', 'true_answer', 'order')

class ProcessedDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessedData
        fields = ('id', 'list_id', 'category', 'order', 'answer', 'status')

class IncomingDataSerializer(serializers.Serializer):
    answer = serializers.CharField(max_length=255)
    order = serializers.IntegerField()

class ProcessDataSerializer(serializers.Serializer):
    list_id = serializers.IntegerField()
    data = IncomingDataSerializer(many=True)