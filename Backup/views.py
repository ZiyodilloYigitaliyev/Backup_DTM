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

            backups_saved = []
            with transaction.atomic():
                for item in incoming_data:
                    list_id = item.get("list_id")
                    true_answer = item.get("true_answer")
                    order = item.get("order")
                    
                    if list_id is None or order is None:
                        return Response(
                            {"error": "list_id and order are required."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Duplikat bo‘lsa, list_id va orderni o‘zgartiramiz
                    #list_id, order = self.get_unique_list_id_order(list_id, order)

                    backup_obj, created = Backup.objects.update_or_create(
                        list_id=list_id,
                        order=order,
                        defaults={"true_answer": true_answer}
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
        # Eng oxirgi Backup obyektini olish (agar mavjud bo'lsa)
            last_backup = Backup.objects.last()
            if last_backup:
                return Response({"list_id": last_backup.list_id}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "Hech qanday backup topilmadi."},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {"error": f"Xatolik yuz berdi: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def delete(self, request, *args, **kwargs):
        try:
            # URL query parameter orqali list_id olinadi
            list_id = request.query_params.get('list_id')
            if not list_id:
                return Response(
                    {"error": "O'chirish uchun list_id parametri talab qilinadi."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # list_id bo'yicha backup obyektlarini qidiramiz
            backups = Backup.objects.filter(list_id=list_id)
            if not backups.exists():
                return Response(
                    {"error": f"list_id {list_id} bilan backup topilmadi."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Topilgan backup obyektlarini o'chiramiz
            count, _ = backups.delete()

            return Response(
                {"success": f"{count} ta backup o'chirildi."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Xatolik yuz berdi: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
