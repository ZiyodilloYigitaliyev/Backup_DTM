from rest_framework.response import Response
from rest_framework import status, viewsets
from .models import ProcessedData
from .serializers import ProcessedDataSerializer

class ProcessedDataViewSet(viewsets.ModelViewSet):
    queryset = ProcessedData.objects.all()
    serializer_class = ProcessedDataSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        list_id = data.get("list_id")
        phone_number = data.get("phone_number")
        order = data.get("order")

        # Integer diapazon tekshiruvi
        try:
            if list_id is not None:
                list_id = int(list_id)
                if list_id > 9223372036854775807 or list_id < -9223372036854775808:
                    return Response({"error": "list_id is out of range"}, status=status.HTTP_400_BAD_REQUEST)
            
            if phone_number is not None:
                phone_number = int(phone_number)
                if phone_number > 999999999999:
                    return Response({"error": "Phone number is too large"}, status=status.HTTP_400_BAD_REQUEST)
            
            if order is not None:
                order = int(order)
                if order > 2147483647 or order < -2147483648:
                    return Response({"error": "order is out of range"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Invalid number format"}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)
