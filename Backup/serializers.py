from .models import Mapping_Data
from rest_framework import serializers

class BackupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mapping_Data
        fields = '__all__'