from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Mapping_Data, Result_Data, Data
from .serializers import ResultDataInputSerializer

class ResultDataCreateAPIView(APIView):
    def post(self, request):
        serializer = ResultDataInputSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data

            # Asosiy maydonlarni ajratib olish
            image_url = validated_data.get('image_url')
            coordinates = validated_data.get('coordinates')
            user_id_val = coordinates.get('user_id')
            phone_val = coordinates.get('phone')
            data_items = coordinates.get('data')

            # Agar shu user_id uchun Result_Data allaqachon mavjud bo'lsa, xatolik xabarini qaytarish
            if Result_Data.objects.filter(list_id=user_id_val).exists():
                return Response(
                    {"error": "Result_Data already exists for this user_id."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Yangi Result_Data yozuvini yaratish
            result_instance = Result_Data.objects.create(
                list_id=user_id_val,
                image_url=image_url,
                phone=phone_val
            )

            # Har bir data elementini Mapping_Data bilan solishtirish va Data modeliga saqlash
            for item in data_items:
                order_value = item.get('order')
                value_val = item.get('value')

                try:
                    mapping_obj = Mapping_Data.objects.get(list_id=user_id_val, order=order_value)
                    category_val = mapping_obj.category
                    status_val = (mapping_obj.true_answer == value_val)
                except Mapping_Data.DoesNotExist:
                    # Agar mos yozuv topilmasa, category null va status False bo'ladi.
                    category_val = None
                    status_val = False

                Data.objects.create(
                    user_id=result_instance,
                    order=order_value,
                    value=value_val,
                    category=category_val,
                    status=status_val
                )

            return Response(
                {"message": "Data saved successfully."},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
