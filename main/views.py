from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ProcessedData

class ProcessDataView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        list_id = data.get("list_id")
        image_url = data.get("image_url", "")
        phone_number = data.get("phone_number")
        incoming_data = data.get("data", [])

        if not isinstance(incoming_data, list):
            return Response({"error": "Invalid format for 'data'. Expected a list."}, status=status.HTTP_400_BAD_REQUEST)

        response_data = []

        for item in incoming_data:
            if not isinstance(item, dict):
                return Response({"error": "Each item in 'data' must be a dictionary."}, status=status.HTTP_400_BAD_REQUEST)

            answer = item.get("answer", "")
            incoming_order = item.get("order")
            status_flag = item.get("status", False)

            processed_entry = ProcessedData.objects.create(
                list_id=list_id,
                phone_number=phone_number,
                order=incoming_order,
                answer=answer,
                status=status_flag
            )
            response_data.append({
                "list_id": list_id,
                "phone_number": phone_number,
                "order": incoming_order,
                "answer": answer,
                "status": status_flag
            })

        return Response(
            {"processed_data": response_data, "image_url": image_url},
            status=status.HTTP_200_OK,
        )
