import csv
import io
import uuid
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

logger = logging.getLogger(__name__)

STUDENT_COORDINATES_PATH = "student_coordinates.csv"  # Student ID CSV manzili

def load_coordinates(csv_path):
    """
    CSV faylni yuklab, koordinatalarni (x, y) juftliklari sifatida to'plamga joylaydi.
    """
    data = set()
    try:
        with open(csv_path, 'r', encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader, None)  # Sarlavhani o'tkazib yuborish
            for row in reader:
                if len(row) < 2:  # Agar noto‘g‘ri qatorda kam element bo‘lsa
                    continue
                try:
                    x, y = row[0].strip(), row[1].strip()
                    if x and y:  # Bo‘sh bo‘lmagan qiymatlarni tekshirish
                        data.add((int(x), int(y)))
                except ValueError:
                    logger.warning("Noto‘g‘ri koordinata: %s", row)
                    continue
        return data
    except FileNotFoundError:
        logger.error("CSV fayl topilmadi: %s", csv_path)
        return set()

def validate_coordinates(bubbles, coordinates_set, threshold=6):
    """
    Kiritilgan koordinatalarni CSV faylidagi ma'lumotlar bilan solishtiradi.
    """
    def is_nearby(coord, coordinates_set):
        x, y = coord
        return any(abs(x - cx) <= threshold and abs(y - cy) <= threshold for cx, cy in coordinates_set)

    return all(is_nearby(coord, coordinates_set) for coord in bubbles)

def classify_coordinates(bubbles):
    """
    Koordinatalarni `student_id`, `phone_number` yoki `bubbles` sifatida tasniflaydi.
    """
    bubbles = list(bubbles)  # To‘plamni ro‘yxatga o‘tkazish
    student_id_coords = bubbles[:2]
    phone_number_coords = bubbles[2:9]
    bubble_coords = bubbles[9:] if len(bubbles) > 9 else []

    return student_id_coords, phone_number_coords, bubble_coords


class ProcessImageView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        transaction_id = str(uuid.uuid4())[:8]
        try:
            image_url = request.data.get('image_url')
            coordinates = request.data.get('coordinates')

            if not image_url or not coordinates:
                logger.error("Majburiy maydonlar yetishmayapti")
                return Response({"error": "image_url va coordinates majburiy"}, status=status.HTTP_400_BAD_REQUEST)

            logger.info("Qabul qilingan ma'lumotlar: %s", {"image_url": image_url, "coordinates": coordinates})

            # Koordinatalarni setga joylash
            coordinates_set = set()
            for coord in coordinates:
                try:
                    x, y = float(coord[0]), float(coord[1])
                    coordinates_set.add((x, y))
                except (ValueError, IndexError):
                    logger.warning("Noto‘g‘ri koordinata: %s", coord)
                    continue

            logger.info("Qabul qilingan koordinatalar soni: %d", len(coordinates_set))

            # CSV fayldagi ma'lumotlar bilan taqqoslash
            all_coordinates_set = load_coordinates(STUDENT_COORDINATES_PATH)
            if not validate_coordinates(coordinates_set, all_coordinates_set):
                logger.error("CSV fayl noto‘g‘ri ma'lumotlarni o‘z ichiga olgan")
                return Response({"error": "Koordinatalar noto‘g‘ri"}, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "message": "Koordinatalar tasdiqlandi",
                "transaction_id": transaction_id
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Xatolik: {e}")
            return Response({"error": f"Xatolik yuz berdi: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
