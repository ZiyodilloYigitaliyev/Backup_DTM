from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
import logging
from .models import ProcessedData, ProcessedTest, ProcessedTestResult, Mapping_Data

class ResultAPIView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            # 1. So'rovdan image_url va coordinates ma'lumotlarini olish
            image_url = request.data.get("image_url")
            coordinates = request.data.get("coordinates", [])
            if not image_url or not coordinates:
                return Response(
                    {"error": "image_url va coordinates majburiy!"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 2. Koordinatalarning to'g'ri formatda ekanligini tekshirish
            valid_coords = [
                coord for coord in coordinates 
                if isinstance(coord, dict) and "x" in coord and "y" in coord
            ]
            if not valid_coords:
                return Response(
                    {"error": "coordinates noto'g'ri formatda!"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 3. ProcessedData dan ma'lumotlarni kategoriya bo'yicha yig'ish:
            #    Bizda uchta kategoriya: "user_id", "phone", "answer"
            results = {"user_id": [], "phone": [], "answer": []}
            for coord in valid_coords:
                x, y = coord["x"], coord["y"]
                matched_data = ProcessedData.objects.filter(
                    Q(x_coord__range=(x - 5, x + 5)) & Q(y_coord__range=(y - 5, y + 5))
                ).order_by("x_coord")
                for data in matched_data:
                    if data.category in results:
                        results[data.category].append({
                            "data_type": data.data_type,   # Bu qiymat keyinchalik Mapping_Data.order bilan solishtiriladi
                            "x_coord": data.x_coord,
                            "y_coord": data.y_coord,
                            "answer": data.answer,
                        })
            
            if not any(results.values()):
                return Response(
                    {"error": "Mos keluvchi koordinatalar topilmadi!"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 4. "user_id" ni aniqlash: "user_id" kategoriyasidagi barcha data_type qiymatlarini birlashtiramiz
            user_results = sorted(results["user_id"], key=lambda item: item["x_coord"])
            user_id_str = "".join([res["data_type"] for res in user_results]) if user_results else None
            if not user_id_str:
                return Response(
                    {"error": "User ID ma'lumotlari topilmadi!"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Agar user_id raqamli bo'lsa, int ga aylantiramiz
            try:
                user_id_int = int(user_id_str)
            except ValueError:
                return Response(
                    {"error": "User ID raqamli formatda emas!"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 5. Mapping_Data modelidan user_id uchun mos yozuvni olish 
            #    (ProcessedData dan hosil bo'lgan user_id, Mapping_Data dagi list_id bilan solishtiriladi)
            mapping_user = Mapping_Data.objects.filter(list_id=user_id_int).first()
            if not mapping_user:
                return Response(
                    {"error": "Mapping_Data da user_id uchun mos yozuv topilmadi!"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 6. "phone" kategoriyasidagi ma'lumotlardan telefon raqamni aniqlash
            phone_results = sorted(results["phone"], key=lambda item: item["x_coord"])
            phone_number = "".join([res["data_type"] for res in phone_results]) if phone_results else None
            
            # 7. ProcessedTest obyektini yaratish yoki yangilash
            processed_test, created = ProcessedTest.objects.get_or_create(
                phone_number=phone_number if phone_number else "Unknown",
                defaults={
                    "file_url": image_url,
                    "total_score": 0,
                }
            )
            if not created:
                processed_test.file_url = image_url
                processed_test.total_score = 0
                processed_test.save()
            
            # 8. Javoblarni tekshirish va Mapping_Data bilan solishtirish
            mapped_answers = []
            for answer_data in results["answer"]:
                # Avvalo, ProcessedData dagi data_type qiymatini raqamga aylantiramiz
                try:
                    data_type_int = int(answer_data["data_type"])
                except ValueError:
                    return Response(
                        {"error": "ProcessedData dagi data_type raqamli emas!"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Mapping_Data modelidan, order maydoni data_type_int ga teng yozuvni topamiz
                mapping_answer = Mapping_Data.objects.filter(order=data_type_int).first()
                if not mapping_answer:
                    return Response(
                        {"error": "Mapping_Data da order ga mos yozuv topilmadi!"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                # Endi, ProcessedData dagi answer qiymatini Mapping_Data dagi true_answer bilan solishtiramiz
                if answer_data["answer"] is None:
                    return Response(
                        {"error": "Answer maydoni bo'sh!"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                is_correct = (answer_data["answer"].strip() == mapping_answer.true_answer.strip())
                
                # Javob to'g'ri bo'lsa, kategoriya (mapping_answer.category) ga qarab ball beramiz
                score = 0
                if is_correct:
                    if mapping_answer.category and mapping_answer.category.startswith("Majburiy_fan"):
                        score = 1.1
                    elif mapping_answer.category and mapping_answer.category.startswith("Fan_1"):
                        score = 2.1
                    elif mapping_answer.category and mapping_answer.category.startswith("Fan_2"):
                        score = 3.1
                
                # ProcessedTestResult obyektini yaratish (order maydoni sifatida mapping_answer.order saqlanadi)
                ProcessedTestResult.objects.create(
                    student=processed_test,
                    student_answer=answer_data["answer"],
                    order=mapping_answer.order,
                    is_correct=is_correct,
                    score=score,
                )
                mapped_answers.append({
                    "answer": answer_data["answer"],
                    "order": mapping_answer.order,
                    "is_correct": is_correct,
                    "score": score,
                })
            
            # 9. Yakuniy ballni hisoblash va ProcessedTest obyektini yangilash
            total_score = sum(item["score"] for item in mapped_answers if item["is_correct"])
            processed_test.total_score = total_score
            processed_test.save()
            
            response_data = {
                "image_url": image_url,
                "user_id": user_id_int,
                "phone_number": phone_number,
                "answers": mapped_answers,
                "total_score": total_score,
                "message": "Koordinatalar muvaffaqiyatli qayta ishlangan!"
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error: {str(e)}")
            return Response(
                {"error": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
