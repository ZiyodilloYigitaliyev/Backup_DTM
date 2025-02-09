from django.http import JsonResponse
import json
from .serializers import MappingDataSerializer, ProcessedDataSerializer
from Backup.models import Mapping_Data
from main.models import ProcessedData
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class ProcessDataView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ProcessedDataSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        list_id = validated_data['list_id']
        incoming_data = validated_data['data']
        phone_number = validated_data['phone_number']

        # Save phone number
        PhoneNumber.objects.create(phone_number=phone_number)

        existing_data = Mapping_Data.objects.filter(list_id=list_id)
        response_data = []

        for item in incoming_data:
            answer = item['answer']
            incoming_order = item['order']

            matching_data = existing_data.filter(order=incoming_order)

            for match in matching_data:
                status = match.true_answer == answer

                processed_entry = ProcessedData.objects.create(
                    list_id=list_id,
                    category=match.category,
                    order=match.order,  # Save order from Mapping_Data
                    answer=answer,
                    status=status
                )

                response_data.append(ProcessedDataSerializer(processed_entry).data)

        return Response({"processed_data": response_data}, status=status.HTTP_200_OK)