import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

logger = logging.getLogger(__name__)

# Saqlangan ma'lumotlar uchun vaqtinchalik ro‘yxat
SAVED_DATA = []

class ProcessImageView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """Saqlangan ma'lumotlarni qaytaradi."""
        return Response({"saved_data": SAVED_DATA}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """Kelgan ma'lumotni saqlaydi va uni qaytaradi."""
        try:
            image_url = request.data.get('image_url')
            coordinates = request.data.get('coordinates')

            if not image_url or not coordinates:
                return Response({"error": "image_url va coordinates majburiy"}, status=status.HTTP_400_BAD_REQUEST)

            data_entry = {
                "image_url": image_url,
                "coordinates": coordinates
            }

            SAVED_DATA.append(data_entry)  # Ma'lumotni saqlash

            return Response(data_entry, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Xatolik: {e}")
            return Response({"error": f"Xatolik yuz berdi: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
