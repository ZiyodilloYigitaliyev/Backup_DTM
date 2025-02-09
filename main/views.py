from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Mapping_Data, ProcessedData

class ProcessDataView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        list_id = data.get("list_id")
        incoming_data = data.get("data", [])
        image_url = data.get("image_url", "")
        phone_number = data.get("phone_number", None)

        if phone_number:
            ProcessedData.objects.create(phone_number=phone_number)

        existing_data = Mapping_Data.objects.filter(list_id=list_id)
        response_data = []

        for item in incoming_data:
            category = item.get("category", "unknown")
            answer = item.get("answer", "")
            incoming_order = item.get("order")
            status_flag = item.get("status", "pending")

            matching_data = existing_data.filter(order=incoming_order)

            for match in matching_data:
                true_status = match.true_answer == answer

                processed_entry = ProcessedData.objects.create(
                    list_id=list_id,
                    category=category,
                    order=match.order,
                    answer=answer,
                    status=true_status
                )
                response_data.append({
                    "list_id": list_id,
                    "category": category,
                    "order": match.order,
                    "answer": answer,
                    "status": true_status
                })

        return Response(
            {"processed_data": response_data, "image_url": image_url},
            status=status.HTTP_200_OK,
        )
