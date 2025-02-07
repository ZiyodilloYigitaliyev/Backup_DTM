from django.http import JsonResponse
from .models import Mapping_Data, ProcessedID
from rest_framework.permissions import AllowAny
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .serializers import MappingDataSerializer

class BackupDataView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            incoming_data = request.data
            print(incoming_data)
            if not isinstance(incoming_data, list, dict):
                return Response({"error": "Payload format must be a list of dictionaries."},
                                status=status.HTTP_400_BAD_REQUEST)

            backups_saved = []

            with transaction.atomic():
                for item in incoming_data:
                    list_id = item.get("list_id")
                    category = item.get("category")
                    true_answer = item.get("true_answer")
                    order = item.get("order")

                    if list_id is None or order is None:
                        return Response({"error": "list_id and order are required."},
                                        status=status.HTTP_400_BAD_REQUEST)

                    # ProcessedID obyektini qidirish
                    processed_id_obj = ProcessedID.objects.filter(list_id=list_id).first()
                    if not processed_id_obj:
                        return Response({"error": f"ProcessedID with list_id {list_id} not found."},
                                        status=status.HTTP_404_NOT_FOUND)

                    # Mapping_Data obyektini yaratish
                    mapping_data_obj = Mapping_Data.objects.create(
                        true_answersID=processed_id_obj,
                        category=category,
                        true_answer=true_answer,
                        order=order
                    )

                    backups_saved.append({
                        "list_id": mapping_data_obj.true_answersID.list_id,
                        "category": mapping_data_obj.category,
                        "true_answer": mapping_data_obj.true_answer,
                        "order": mapping_data_obj.order
                    })

            return Response(
                {"success": "Mapping data saved successfully.", "data": backups_saved},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
                
    def get(self, request, *args, **kwargs):
        try:
            last_entry = ProcessedID.objects.order_by('-id').first()  # Eng oxirgi yozuvni olish
            if last_entry:
                return Response({"list_id": last_entry.list_id}, status=status.HTTP_200_OK)
            else:
                return Response({"list_id": None}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Xatolik yuz berdi: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                backups = Mapping_Data.objects.all()
                if not backups.exists():
                    return Response(
                        {"error": "No backup exists to delete."},
                        status=status.HTTP_404_NOT_FOUND
                    )
                count, _ = backups.delete()
                return Response(
                    {"success": f"{count} backups deleted."},
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            return Response(
                {"error": f"An error occurred during deletion: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
