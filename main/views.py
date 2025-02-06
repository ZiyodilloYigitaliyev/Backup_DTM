from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ProcessedData, Mapping_Data

class ListIDAPIView(APIView):
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

            results = []
            for coord in valid_coords:
                x, y = coord["x"], coord["y"]

                # ProcessedData bazasidan mos keluvchi koordinatalarni qidirish
                matched_data = ProcessedData.objects.filter(
                    Q(x_coord__range=(x - 5, x + 5)) & Q(y_coord__range=(y - 5, y + 5))
                ).order_by("x_coord")  # Min x bo‘yicha tartib

                for data in matched_data:
                    results.append({
                        "data_type": data.data_type,
                        "x_coord": data.x_coord,
                        "y_coord": data.y_coord,
                    })

            # Agar hech qanday moslik topilmasa
            if not results:
                return Response(
                    {"error": "Mos keluvchi koordinatalar topilmadi!"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Aniqlangan `data_type`larni minimal x bo‘yicha tartiblash va birlashtirish
            sorted_results = sorted(results, key=lambda item: item["x_coord"])
            concatenated_data = "".join([res["data_type"] for res in sorted_results])

            # Aniqlangan `list_id`ni Mapping_Data modelida tekshirish
            mapping_data_obj = Mapping_Data.objects.filter(list_id=int(concatenated_data)).first()
            if not mapping_data_obj:
                return Response(
                    {"error": f"Mapping_Data jadvalida list_id '{concatenated_data}' topilmadi!"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Mapping_Data modeli orqali kerakli natijani olish
            response_data = {
                "image_url": image_url,
                "list_id": concatenated_data,
                "true_answer": mapping_data_obj.true_answer,
                "order": mapping_data_obj.order,
                "message": "Koordinatalar muvaffaqiyatli qayta ishlangan va Mapping_Data topildi!",
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
