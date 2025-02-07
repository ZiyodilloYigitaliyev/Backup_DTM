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
            if not isinstance(incoming_data, list):
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

                    # list_id bo'yicha ProcessedID bazada mavjudligini tekshiramiz
                    processed_id_obj = ProcessedID.objects.filter(list_id=list_id).first()
                    if not processed_id_obj:
                        return Response({"error": f"ProcessedID with list_id {list_id} not found."},
                                        status=status.HTTP_404_NOT_FOUND)

                    # Mapping_Data'ni olish yoki yaratish
                    backup_obj, created = Mapping_Data.objects.get_or_create(answer=processed_id_obj)

                    # Eski true_answer va order listiga yangi ma'lumotlarni qo'shamiz
                    if not isinstance(backup_obj.true_answer, list):
                        backup_obj.true_answer = []
                    if not isinstance(backup_obj.order, list):
                        backup_obj.order = []
                    if not isinstance(backup_obj.category, list):
                        backup_obj.category = []

                    backup_obj.true_answer.append(true_answer)
                    backup_obj.category.append(category)
                    backup_obj.order.append(order)
                    backup_obj.save()

                    backups_saved.append({
                        "list_id": backup_obj.answer.list_id,
                        "category": backup_obj.category,
                        "true_answer": backup_obj.true_answer,
                        "order": backup_obj.order
                    })

            return Response(
                {"success": "Backup data saved successfully.", "data": backups_saved},
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
                return Response({"list_id": last_entry.answer.list_id}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Hech qanday ma'lumot topilmadi"})
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
