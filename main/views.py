from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from .models import Mapping_Data, Result_Data, Data, PDFResult
from .serializers import ResultDataInputSerializer
from .utils import generate_pdf

class ResultDataCreateAPIView(APIView):
    # Faqat JSON ma'lumotlarni qabul qilish uchun
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

            # Shu user_id uchun allaqachon Result_Data mavjud bo'lsa, xatolik qaytaramiz
            if Result_Data.objects.filter(list_id=user_id_val).exists():
                return Response(
                    {"error": "Bu user_id uchun natija allaqachon mavjud."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Global mapping: birinchi mavjud yozuv asosida school va question_class ni olamiz
            mapping_obj_global = Mapping_Data.objects.filter(list_id=user_id_val).first()
            school_val = mapping_obj_global.school if mapping_obj_global and mapping_obj_global.school else ""
            question_class_val = mapping_obj_global.question_class if mapping_obj_global and mapping_obj_global.question_class is not None else 0

            # Yangi Result_Data yozuvini yaratish (yangi maydonlar bilan)
            result_instance = Result_Data.objects.create(
                list_id=user_id_val,
                image_url=image_url,
                phone=phone_val,
                school=school_val,
                question_class=question_class_val
            )

            # Har bir data elementini saqlash
            for item in data_items:
                order_value = item.get('order')
                value_val = item.get('value')

                try:
                    mapping_obj = Mapping_Data.objects.get(list_id=user_id_val, order=order_value)
                    category_val = mapping_obj.category
                    subject_val = mapping_obj.subject  # yangi maydon
                    status_val = (mapping_obj.true_answer == value_val)
                except Mapping_Data.DoesNotExist:
                    # Agar mos yozuv topilmasa
                    category_val = None
                    subject_val = None
                    status_val = False

                Data.objects.create(
                    user_id=result_instance,
                    order=order_value,
                    value=value_val,
                    category=category_val,
                    subject=subject_val,  # yangi maydon
                    status=status_val
                )

            # PDF uchun ma'lumotlarni yig'ish
            pdf_data = {
                'id': user_id_val,
                'phone': phone_val,
                'image': image_url,
                'results': []
            }

            # Bog'langan barcha Data obyektlarini olish
            data_objects = Data.objects.filter(user_id=result_instance)
            for item in data_objects:
                pdf_data['results'].append({
                    'number': item.order,             # order maydonini number deb qabul qilamiz
                    'option': item.value,              # value maydoni
                    'category': item.category if item.category else "",
                    'subject': item.subject if item.subject else "",  # yangi maydon
                    'status': str(item.status)         # Boolean qiymatni stringga aylantiramiz
                })

            # PDF hosil qilish va PDFResult modelida saqlash
            pdf_url = generate_pdf(pdf_data)

            return Response(
                {"message": "Data saqlandi va PDF yaratildi.", "pdf_url": pdf_url},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResultDataByDateRetrieveAPIView(APIView):
    """
    Query parametri orqali berilgan sana (YYYY-MM-DD) bo'yicha natijalarni qaytaruvchi view.
    """
    def get(self, request, *args, **kwargs):
        date_str = request.query_params.get('date')
        if not date_str:
            return Response(
                {"error": "date query parametri talab qilinadi. (Format: YYYY-MM-DD)"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Sana formatini tekshiramiz
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Noto'g'ri sana formati. Iltimos YYYY-MM-DD formatidan foydalaning."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Result_Data modelida created_at maydoni orqali filtrlaymiz
        results = Result_Data.objects.filter(created_at__date=date_obj)
        if not results.exists():
            return Response(
                {"error": "Berilgan sana uchun natijalar topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )

        response_data = []
        for result in results:
            # Natija bilan bog'liq Data obyektlarini yig'amiz
            data_objects = Data.objects.filter(user_id=result)
            data_list = []
            for item in data_objects:
                data_list.append({
                    "order": item.order,
                    "value": item.value,
                    "category": item.category if item.category else "",
                    "subject": item.subject if item.subject else "",
                    "status": item.status
                })

            response_data.append({
                "user_id": result.list_id,
                "phone": result.phone,
                "school": result.school,
                "question_class": result.question_class,
                "created_at": result.created_at,  # created_at maydoni
                "data": data_list
            })

        return Response(response_data, status=status.HTTP_200_OK)

# PDF natijani olish uchun GET view
class PDFResultRetrieveAPIView(APIView):
    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id')  # user_id ni query parametrlardan olish
        
        if not user_id:
            return Response({"error": "user_id parametri talab qilinadi."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pdf_result = PDFResult.objects.get(user_id=user_id)
            data = {
                "user_id": pdf_result.user_id,
                "phone": pdf_result.phone,
                "pdf_url": pdf_result.pdf_url  # To‘g‘ri maydon nomi
            }
            return Response(data, status=status.HTTP_200_OK)
        except PDFResult.DoesNotExist:
            return Response({"error": "Bu user_id uchun PDF topilmadi."}, status=status.HTTP_404_NOT_FOUND)
