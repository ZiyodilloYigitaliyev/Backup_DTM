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
        if serializer.is_valid():
            validated_data = serializer.validated_data
            list_id = validated_data.get("list_id")
            incoming_data = validated_data.get("data", [])
            image_url = validated_data.get("image_url", "")

            phone_number = validated_data.get("phone_number", None)
            if phone_number:
                phone_number.objects.create(phone_number=phone_number)

            existing_data = Mapping_Data.objects.filter(list_id=list_id)
            response_data = []

            for item in incoming_data:
                category = item.get("category", "unknown")
                answer = item.get("answer", "")
                incoming_order = item.get("order")
                status_value = item.get("status", "pending")

                matching_data = existing_data.filter(order=incoming_order)

                for match in matching_data:
                    true_status = match.true_answer == answer

                    processed_entry = ProcessedData.objects.create(
                        list_id=list_id,
                        category=category,
                        order=match.order,  # Mapping_Data'dan order ni saqlash
                        answer=answer,
                        status=true_status
                    )

                    response_data.append(ProcessedDataSerializer(processed_entry).data)

            return Response(
                {"processed_data": response_data, "image_url": image_url},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
