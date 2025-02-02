from django.shortcuts import render
from .models import Backup
from rest_framework.permissions import AllowAny
from django.db import transaction
from rest_framework.response import Response
from sympy import Max
from rest_framework.views import APIView
from rest_framework import status
import requests
# Create your views here.


class BackupDataView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            incoming_data = request.data

            if not isinstance(incoming_data, list):
                return Response(
                    {"error": "Payload format must be a list of dictionaries."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Guruhlash: har bir list_id uchun true_answer va order ni yig'amiz
            grouped_data = {}
            for item in incoming_data:
                list_id = item.get("list_id")
                true_answer = item.get("true_answer")
                order = item.get("order")
                
                if list_id is None or order is None:
                    return Response(
                        {"error": "list_id and order are required."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                if list_id not in grouped_data:
                    grouped_data[list_id] = {"true_answer": [], "order": []}
                
                grouped_data[list_id]["true_answer"].append(true_answer)
                grouped_data[list_id]["order"].append(order)
            
            backups_saved = []
            with transaction.atomic():
                # Har bir guruh bo'yicha yozuvni update_or_create qilamiz
                for list_id, values in grouped_data.items():
                    backup_obj, created = Backup.objects.update_or_create(
                        list_id=list_id,
                        defaults={
                            "true_answer": values["true_answer"],
                            "order": values["order"]
                        }
                    )
                    backups_saved.append({
                        "list_id": backup_obj.list_id,
                        "true_answer": backup_obj.true_answer,
                        "order": backup_obj.order,
                        "created": created
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
            # Oxirgi list_id ni olish: Backup obyektlarini list_id bo‘yicha kamayish tartibida saralash
            last_backup = Backup.objects.order_by("-list_id").first()
            if last_backup:
                return Response({"list_id": last_backup.list_id}, status=status.HTTP_200_OK)
            else:
                # Agar backuplar mavjud bo‘lmasa, None yoki boshqa default qiymat qaytarish mumkin
                return Response({"list_id": None}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )


    def delete(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                backups = Backup.objects.all()
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
