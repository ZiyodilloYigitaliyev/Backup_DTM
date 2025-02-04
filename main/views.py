import logging
import os
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from conf.settings import BASE_DIR

logger = logging.getLogger(__name__)

# Saqlangan ma'lumotlar uchun vaqtinchalik ro‘yxat
SAVED_DATA = []
COORDINATES_PATH = os.path.join(BASE_DIR, 'app/coordinates/coordinates.json')

def load_coordinates():
    """JSON fayldan koordinatalarni yuklash."""
    if os.path.exists(COORDINATES_PATH):
        with open(COORDINATES_PATH, 'r', encoding='utf-8') as file:
            try:
                return json.load(file).get("coordinates", [])
            except json.JSONDecodeError:
                logger.error("JSON faylni o'qishda xatolik yuz berdi.")
                return []
    return []

class ProcessImageView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """Saqlangan ma'lumotlarni qaytaradi."""
        return Response({"saved_data": SAVED_DATA}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """Kelgan ma'lumotni saqlaydi va uni qaytaradi."""
        try:
            image_url = request.data.get('image_url')
            user_coordinates = request.data.get('coordinates')

            if not image_url or not user_coordinates:
                return Response({"error": "image_url va coordinates majburiy"}, status=status.HTTP_400_BAD_REQUEST)

            # JSON fayldan koordinatalarni yuklash
            saved_coordinates = load_coordinates()

            # O'xshash koordinatalarni aniqlash
            matching_coordinates = [coord for coord in user_coordinates if coord in saved_coordinates]

            data = {
                "image_url": image_url,
                "user_coordinates": user_coordinates,
                "matching_coordinates": matching_coordinates
            }

            SAVED_DATA.append(data)  # Ma'lumotni saqlash

            return Response(data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Xatolik: {e}")
            return Response({"error": f"Xatolik yuz berdi: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        """Barcha saqlangan ma'lumotlarni o‘chiradi."""
        global SAVED_DATA
        SAVED_DATA.clear()
        return Response({"message": "Barcha ma'lumotlar o‘chirildi"}, status=status.HTTP_200_OK)