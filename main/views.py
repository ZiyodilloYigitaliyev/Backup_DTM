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
            serializer.save()

            validated_data = serializer.validated_data
            list_id = validated_data['list_id']
            incoming_data = validated_data['data']
            phone_number = validated_data['phone_number']

            # Telefon raqamini saqlash
            phone_number.objects.create(phone_number=phone_number)

            existing_data = Mapping_Data.objects.filter(list_id=list_id)
            response_data = []

            for item in incoming_data:
                answer = item['answer']
                incoming_order = item['order']

                matching_data = existing_data.filter(order=incoming_order)

                for match in matching_data:
                    status_value = match.true_answer == answer

                    processed_entry = ProcessedData.objects.create(
                        list_id=list_id,
                        category=match.category,
                        order=match.order,  # Mapping_Data'dan order ni saqlash
                        answer=answer,
                        status=status_value
                    )

                    response_data.append(ProcessedDataSerializer(processed_entry).data)

            return Response({"processed_data": response_data}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
