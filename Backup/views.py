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

            # Ma'lumot "data" kaliti ostida ro'yxat shaklida kelishi kerak
            if not isinstance(incoming_data, dict) or "data" not in incoming_data:
                return Response(
                    {"error": "Payload format must be {'data': [...]}."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            data_list = incoming_data["data"]
            if not isinstance(data_list, list):
                return Response(
                    {"error": "The 'data' value must be a list."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            backups_saved = []
            with transaction.atomic():
                for item in data_list:
                    list_id = item.get("list_id")
                    true_answer = item.get("true_answer")
                    order = item.get("order")
                    
                    # Tekshiruv: majburiy maydonlar bo'lishi kerak
                    if list_id is None or true_answer is None or order is None:
                        return Response(
                            {"error": "list_id, true_answer, and order are required."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Agar mavjud yozuv bo'lsa update qiladi, aks holda yangi yozuv yaratadi.
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
            backups = Backup.objects.all()
            data = []
            for backup in backups:
                data.append({
                    "list_id": backup.list_id,
                    "true_answer": backup.true_answer,
                    "order": backup.order,
                })
            return Response({"data": data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    # Agar sizga unique yoki keyingi qiymat kerak bo'lsa, quyidagi yordamchi funksiyalarni qo'shishingiz mumkin.
    def _get_unique_value(self, field_name, current_value):
        filter_kwargs = {field_name: current_value}
        if Backup.objects.filter(**filter_kwargs).exists():
            max_value = Backup.objects.aggregate(max_val=Max(field_name))['max_val'] or current_value
            return max_value + 1
        else:
            return current_value

    def _get_next_value(self, field_name):
        max_value = Backup.objects.aggregate(max_val=Max(field_name))['max_val']
        return (max_value + 1) if max_value is not None else 1
