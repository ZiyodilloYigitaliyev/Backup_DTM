import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

logger = logging.getLogger(__name__)

class ProcessImageView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            image_url = request.data.get('image_url')
            coordinates = request.data.get('coordinates')

            if not image_url or not coordinates:
                return Response({"error": "image_url va coordinates majburiy"}, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "image_url": image_url,
                "coordinates": coordinates
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Xatolik: {e}")
            return Response({"error": f"Xatolik yuz berdi: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
