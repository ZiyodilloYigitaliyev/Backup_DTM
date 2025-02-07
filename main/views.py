from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ProcessedData, Mapping_Data, ProcessedTest, ProcessedTestResult
import logging
class ResultAPIView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            # Requestdan image_url va coordinates ma'lumotlarini olish
            image_url = request.data.get("image_url")
            coordinates = request.data.get("coordinates", [])

            if not image_url or not coordinates:
                return Response(
                    {"error": "image_url va coordinates majburiy!"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Koordinatalarni tekshirish
            valid_coords = [
                coord for coord in coordinates if isinstance(coord, dict) and "x" in coord and "y" in coord
            ]

            if not valid_coords:
                return Response(
                    {"error": "coordinates noto‘g‘ri formatda!"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Kategoriya bo'yicha natijalarni yig'ish
            results = {
                "user_id": [],
                "phone": [],
                "answer": [],
            }

            for coord in valid_coords:
                x, y = coord["x"], coord["y"]

                # ProcessedData bazasidan mos keluvchi koordinatalarni qidirish
                matched_data = ProcessedData.objects.filter(
                    Q(x_coord__range=(x - 5, x + 5)) & Q(y_coord__range=(y - 5, y + 5))
                ).order_by("x_coord")  # Min x bo‘yicha tartib

                for data in matched_data:
                    if data.category in results:
                        results[data.category].append({
                            "data_type": data.data_type,
                            "x_coord": data.x_coord,
                            "y_coord": data.y_coord,
                            "answer": data.answer,
                        })

            # Agar hech qanday moslik topilmasa
            if not any(results.values()):
                return Response(
                    {"error": "Mos keluvchi koordinatalar topilmadi!"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # `matching` uchun list_idni aniqlash
            list_id_results = sorted(results["user_id"], key=lambda item: item["x_coord"])
            list_id = "".join([res["data_type"] for res in list_id_results]) if list_id_results else None

            # `phone` uchun telefon raqamni aniqlash
            phone_results = sorted(results["phone"], key=lambda item: item["x_coord"])
            phone_number = "".join([res["data_type"] for res in phone_results]) if phone_results else None

            # `answer` uchun javoblarni aniqlash
            answers = results["answer"]
            mapped_answers = []

            # ProcessedTest obyektini bir marta yaratish
            processed_test = ProcessedTest.objects.create(
                file_url=image_url,
                phone_number=phone_number if phone_number else "Unknown",
                total_score=0,  # Yakuniy ballni keyinroq yangilash
            )

            for answer_data in answers:
                answer = answer_data["answer"]
                is_correct = False
                score = 0

                # Mapping_Data modeli orqali tekshirish
                mapping_data_obj = None
                if mapping_data_obj and mapping_data_obj.order:
                    try:
                        # Javobni `order` ro'yxatida borligini tekshirish
                        is_correct = answer_data["order"] in mapping_data_obj.order
                    except (ValueError, TypeError):
                        is_correct = False
                else:
                    is_correct = False

                if mapping_data_obj:
                    # Javobni `order` bo'yicha tekshirish
                    try:
                        answer_index = mapping_data_obj.order.index(answer_data["order"])
                        if answer_index >= 0:
                            is_correct = True
                    except ValueError:
                        is_correct = False

                    # Kategoriyaga qarab ballni aniqlash
                    if mapping_data_obj.categorys.startswith("Majburiy_fan"):
                        score = 1.1
                    elif mapping_data_obj.categorys.startswith("Fan_1"):
                        score = 2.1
                    elif mapping_data_obj.categorys.startswith("Fan_2"):
                        score = 3.1

                    # Agar javob noto'g'ri bo'lsa, ballni 0 qilish
                    if not is_correct:
                        score = 0

                # Har bir javobni ProcessedTestResult modeliga saqlash
                result = ProcessedTestResult.objects.create(
                    student=processed_test,
                    student_answer=answer,
                    is_correct=is_correct,
                    score=score,
                )
                mapped_answers.append({
                    "answer": answer,
                    "is_correct": is_correct,
                    "score": score,
                })

            # Yakuniy ballni yangilash
            total_score = sum([res["score"] for res in mapped_answers if res["is_correct"]])
            processed_test.total_score = total_score
            processed_test.save()

            # Yakuniy javob
            response_data = {
                "image_url": image_url,
                "list_id": list_id,
                "phone_number": phone_number,
                "answers": mapped_answers,
                "total_score": total_score,
                "message": "Koordinatalar muvaffaqiyatli qayta ishlangan!",
            }

            return Response(response_data, status=status.HTTP_201_CREATED)


        except ValueError as ve:
            return Response({"error": f"ValueError: {str(ve)}"}, status=status.HTTP_400_BAD_REQUEST)
        except ProcessedData.DoesNotExist as pdne:
            return Response({"error": f"ProcessedData not found: {str(pdne)}"}, status=status.HTTP_404_NOT_FOUND)
        except Mapping_Data.DoesNotExist as mdne:
            return Response({"error": f"Mapping_Data not found: {str(mdne)}"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # Log the error for debugging
        
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error: {str(e)}")
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)