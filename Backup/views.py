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
    
    def get_unique_list_id_order(self, list_id, order):
        while Backup.objects.filter(list_id=list_id, order=order).exists():
            list_id += 1
            order += 1
        return list_id, order

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
                    list_id, order = self.get_unique_list_id_order(list_id, order)

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
            data = [
                {"list_id": backup.list_id, "true_answer": backup.true_answer, "order": backup.order}
                for backup in backups
            ]
            return Response({"data": data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )