from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework import status

from .models import Mapping_Data, Result_Data, Data, PDFResult
from .serializers import ResultDataInputSerializer
from .utils import generate_pdf  # generate_pdf funksiyasi joylashgan modulni import qiling


class ResultDataCreateAPIView(APIView):
    # Faqat JSON ma'lumotlarni qabul qilish uchun JSONParser ni o'rnatish
    parser_classes = [JSONParser]

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

            # Agar shu user_id uchun Result_Data allaqachon mavjud bo'lsa, xatolik qaytaramiz
            if Result_Data.objects.filter(list_id=user_id_val).exists():
                return Response(
                    {"error": "Bu user_id uchun natija allaqachon mavjud."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Yangi Result_Data yozuvini yaratish
            result_instance = Result_Data.objects.create(
                list_id=user_id_val,
                image_url=image_url,
                phone=phone_val
            )

            # Har bir data elementini saqlash
            for item in data_items:
                order_value = item.get('order')
                value_val = item.get('value')

                try:
                    mapping_obj = Mapping_Data.objects.get(list_id=user_id_val, order=order_value)
                    category_val = mapping_obj.category
                    status_val = (mapping_obj.true_answer == value_val)
                except Mapping_Data.DoesNotExist:
                    # Agar mos yozuv topilmasa, category None va status False bo'ladi.
                    category_val = None
                    status_val = False

                Data.objects.create(
                    user_id=result_instance,
                    order=order_value,
                    value=value_val,
                    category=category_val,
                    status=status_val
                )

            # PDF uchun kerakli maʼlumotlarni yigʻamiz
            pdf_data = {
                'id': user_id_val,
                'phone': phone_val,
                'image': image_url,
                'results': []
            }

            # Result_Data ga bog'langan barcha Data obyektlarini olib, generate_pdf uchun formatlaymiz
            data_objects = Data.objects.filter(user_id=result_instance)
            for item in data_objects:
                pdf_data['results'].append({
                    'number': item.order,      # 'order' maydonini 'number' deb qabul qilamiz
                    'option': item.value,       # 'value' maydoni
                    'category': item.category if item.category else "",
                    'status': str(item.status)  # True/False qiymatni stringga aylantiramiz
                })

            # PDF hosil qilish va PDFResult modelida saqlash
            generate_pdf(pdf_data)
            # generate_pdf funksiyasi PDFResult modeliga (user_id, phone va pdf_file maydoni orqali) faylni saqlaydi

            return Response(
                {"message": "Data saqlandi va PDF yaratildi."},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# PDF natijani olish uchun GET view
class PDFResultRetrieveAPIView(APIView):
    def get(self, request, user_id):
        try:
            pdf_result = PDFResult.objects.get(user_id=user_id)
            data = {
                "user_id": pdf_result.user_id,
                "phone": pdf_result.phone,
                "pdf_file_url": pdf_result.pdf_file.url  # S3 bucket-ga yuklangan PDF URL
            }
            return Response(data, status=status.HTTP_200_OK)
        except PDFResult.DoesNotExist:
            return Response({"error": "Bu user_id uchun PDF topilmadi."}, status=status.HTTP_404_NOT_FOUND)
