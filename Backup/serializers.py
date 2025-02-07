from .models import Mapping_Data, ProcessedID
from rest_framework import serializers

class MappingDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mapping_Data
        fields = '__all__'

class ProcessedIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessedID
        fields = '__all__'