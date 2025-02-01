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
                {"error": f"Xatolik yuz berdi: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def post(self, request, *args, **kwargs):
        try:
            incoming_data = request.data

            # Agar ma'lumot yagona obyekt sifatida kelsa, uni ro'yxatga o'ramiz
            if isinstance(incoming_data, dict):
                data_list = [incoming_data]
            elif isinstance(incoming_data, list):
                data_list = incoming_data
            else:
                return Response(
                    {"error": "Ma'lumot dictionary yoki ro'yxat shaklida yuborilishi kerak."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            backups_saved = []
            with transaction.atomic():
                for item in data_list:
                    # Faqat list_id, order va true_answer ni olish
                    orig_list_id = item.get("list_id")
                    orig_order = item.get("order")
                    true_answer = item.get("true_answer", "")

                    # Agar list_id yoki order kiritilmagan bo'lsa, ularni bazadagi eng katta qiymatdan birga oshirib aniqlaymiz
                    if orig_list_id is None:
                        list_id = self._get_next_value("list_id")
                    else:
                        list_id = self._get_unique_value("list_id", orig_list_id)

                    if orig_order is None:
                        order = self._get_next_value("order")
                    else:
                        order = self._get_unique_value("order", orig_order)

                    # Yangi yozuvni yaratamiz (faqat kerakli maydonlar bilan)
                    backup_obj = Backup.objects.create(
                        list_id=list_id,
                        order=order,
                        true_answer=true_answer,
                    )
                    backups_saved.append({
                        "list_id": backup_obj.list_id,
                        "true_answer": backup_obj.true_answer,
                        "order": backup_obj.order,
                        "created": True
                    })

            return Response(
                {"success": "Backup malumotlari muvaffaqiyatli saqlandi", "data": backups_saved},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {"error": f"Xatolik yuz berdi: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

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

    def auto_post_backup_data(self, external_url):
        try:
            backups = Backup.objects.all()
            payload = []
            for backup in backups:
                payload.append({
                    "list_id": backup.list_id,
                    "true_answer": backup.true_answer,
                    "order": backup.order,
                })

            headers = {'Content-Type': 'application/json'}
            response = requests.post(external_url, json=payload, headers=headers)
            response.raise_for_status()
            print("Auto post successful. Response status:", response.status_code)
        except Exception as e:
            print("Failed to auto-post data to external url:", e)
