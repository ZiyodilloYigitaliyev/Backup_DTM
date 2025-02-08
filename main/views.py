from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
import logging
# from .models import ProcessedData, ProcessedTest, ProcessedTestResult, Mapping_Data
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import ImageData
from .serializers import ImageDataSerializer

@api_view(["POST"])
def upload_image(request):
    serializer = ImageDataSerializer(data=request.data)
    
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Image data saved successfully"}, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# class ResultAPIView(APIView):
#     def post(self, request, *args, **kwargs):
        
        # try:
        #     # 1. Requestdan image_url va coordinates ma'lumotlarini olish
        #     image_url = request.data.get("image_url")
        #     coordinates = request.data.get("coordinates", [])
        #     if not image_url or not coordinates:
        #         return Response(
        #             {"error": "image_url va coordinates majburiy!"},
        #             status=status.HTTP_400_BAD_REQUEST
        #         )
            
        #     # 2. Koordinatalarning to'g'ri formatda ekanligini tekshirish
        #     valid_coords = [
        #         coord for coord in coordinates
        #         if isinstance(coord, dict) and "x" in coord and "y" in coord
        #     ]
        #     if not valid_coords:
        #         return Response(
        #             {"error": "coordinates noto'g'ri formatda!"},
        #             status=status.HTTP_400_BAD_REQUEST
        #         )
            
        #     # 3. ProcessedData dan ma'lumotlarni kategoriya bo'yicha yig'ish:
        #     results = {"user_id": [], "phone": [], "answer": []}
        #     for coord in valid_coords:
        #         x = coord["x"]
        #         y = coord["y"]
        #         matched_data = ProcessedData.objects.filter(
        #             Q(x_coord__range=(x - 5, x + 5)) & Q(y_coord__range=(y - 5, y + 5))
        #         ).order_by("x_coord")
        #         for data in matched_data:
        #             if data.category in results:
        #                 results[data.category].append({
        #                     "data_type": data.data_type,
        #                     "x_coord": data.x_coord,
        #                     "y_coord": data.y_coord,
        #                     "answer": data.answer,
        #                 })
            
        #     if not any(results.values()):
        #         return Response(
        #             {"error": "Mos keluvchi koordinatalar topilmadi!"},
        #             status=status.HTTP_404_NOT_FOUND
        #         )
            
        #     # 4. "user_id" ni aniqlash:
        #     user_results = sorted(results["user_id"], key=lambda item: item["x_coord"])
        #     user_id_str = "".join([res["data_type"] for res in user_results]) if user_results else None
        #     if not user_id_str:
        #         return Response(
        #             {"error": "User ID ma'lumotlari topilmadi!"},
        #             status=status.HTTP_400_BAD_REQUEST
        #         )
        #     try:
        #         user_id_int = int(user_id_str)
        #     except ValueError:
        #         return Response(
        #             {"error": "User ID raqamli formatda emas!"},
        #             status=status.HTTP_400_BAD_REQUEST
        #         )
            
        #     # 5. Mapping_Data modelidan user_id uchun mos yozuvni olish (list_id bilan solishtirish)
        #     mapping_user = Mapping_Data.objects.filter(list_id=user_id_int).first()
        #     if not mapping_user:
        #         return Response(
        #             {"error": "Mapping_Data da user_id uchun mos yozuv topilmadi!"},
        #             status=status.HTTP_404_NOT_FOUND
        #         )

        #     # 5.1. list_id bo'yicha qolgan yozuvlarni topish
        #     mapping_list = Mapping_Data.objects.filter(list_id=user_id_int).exclude(order=mapping_user.order)

        #     # 6. "phone" kategoriyasidagi ma'lumotlardan telefon raqamni aniqlash
        #     phone_results = sorted(results["phone"], key=lambda item: item["x_coord"])
        #     phone_number = "".join([res["data_type"] for res in phone_results]) if phone_results else None
            
        #     # 7. ProcessedTest obyektini yaratish yoki yangilash
        #     processed_test, created = ProcessedTest.objects.get_or_create(
        #         phone_number=phone_number if phone_number else "Unknown",
        #         defaults={
        #             "file_url": image_url,
        #             "image_url": image_url,
        #             "total_score": 0,
        #         }
        #     )
        #     if not created:
        #         processed_test.file_url = image_url
        #         processed_test.image_url = image_url
        #         processed_test.total_score = 0
        #         processed_test.save()
            
        #     # 8. Javoblarni tekshirish va Mapping_Data bilan taqqoslash
        #     mapped_answers = []
        #     for answer_data in results["answer"]:
        #         try:
        #             data_type_int = int(answer_data["data_type"])
        #         except ValueError:
        #             return Response(
        #                 {"error": "ProcessedData dagi data_type raqamli emas!"},
        #                 status=status.HTTP_400_BAD_REQUEST
        #             )
                
        #         mapping_answer = Mapping_Data.objects.filter(order=data_type_int).first()
        #         if not mapping_answer:
        #             return Response(
        #             {"error": f"Mapping_Data da order={data_type_int} ga mos yozuv topilmadi!"},
        #             status=status.HTTP_404_NOT_FOUND
        #             )
                
        #         if answer_data["answer"] is None:
        #             return Response(
        #                 {"error": "Answer maydoni bo'sh!"},
        #                 status=status.HTTP_400_BAD_REQUEST
        #             )
                
        #         if mapping_answer and mapping_answer.true_answer and answer_data.get("answer"):
        #             is_correct = (answer_data["answer"].strip() == mapping_answer.true_answer.strip())
        #             score = 0

        #             if is_correct:
        #                 category = mapping_answer.category or ""
        #                 if category.startswith("Majburiy_fan"):
        #                     score = 1.1
        #                 elif category.startswith("Fan_1"):
        #                     score = 2.1
        #                 elif category.startswith("Fan_2"):
        #                     score = 3.1

        #             ProcessedTestResult.objects.create(
        #                 student=processed_test,
        #                 student_answer=answer_data["answer"],
        #                 order=mapping_answer.order,
        #                 is_correct=is_correct,
        #                 score=score,
        #             )

        #             mapped_answers.append({
        #                 "answer": answer_data["answer"],
        #                 "order": mapping_answer.order,
        #                 "is_correct": is_correct,
        #                 "score": score,
        #             })
        #         else:
        #             print("Xatolik: answer_data yoki mapping_answer None qiymatga ega!")

        #     # 9. Yakuniy ballni hisoblash va ProcessedTest obyektini yangilash
        #     total_score = sum(item["score"] for item in mapped_answers if item["is_correct"])
        #     processed_test.total_score = total_score
        #     processed_test.save()
            
        #     response_data = {
        #         "file_url": processed_test.file_url,
        #         "image_url": processed_test.image_url,
        #         "user_id": user_id_int,
        #         "phone_number": phone_number,
        #         "answers": mapped_answers,
        #         "total_score": total_score,
        #         "message": "Koordinatalar muvaffaqiyatli qayta ishlangan!"
        #     }
        #     return Response(response_data, status=status.HTTP_201_CREATED)
        
        # except Exception as e:
        #     logger = logging.getLogger(__name__)
        #     logger.error(f"Unexpected error: {str(e)}")
        #     return Response(
        #         {"error": "An unexpected error occurred."},
        #         status=status.HTTP_500_INTERNAL_SERVER_ERROR
        #     )
