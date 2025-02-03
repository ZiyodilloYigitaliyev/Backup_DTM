import os
import csv
import uuid
import logging
from io import StringIO
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .models import ProcessedTest

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COORDINATES_PATH = os.path.join(BASE_DIR, 'app/coordinates/coordinates.csv')

def load_coordinates(csv_path):
    """ CSV faylni yuklab, koordinatalarni o'qib dictionary sifatida qaytaradi. """
    data = set()
    try:
        with open(csv_path, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Sarlavhani o'tkazib yuborish
            for row in reader:
                try:
                    x, y = float(row[0]), float(row[1])
                    data.add((x, y))
                except (ValueError, IndexError):
                    continue
        return data
    except FileNotFoundError:
        logger.error("CSV fayl topilmadi: %s", csv_path)
        return set()

def validate_coordinates(bubbles, coordinates_set):
    """ Kiritilgan koordinatalarni asosiy CSV fayldagi ma'lumotlar bilan solishtiradi.
        Agar koordinatalar ±6 oralig'ida bo'lsa, haqiqiy deb hisoblanadi. """
    
    def is_nearby(coord, coordinates_set, threshold=6):
        x, y = coord
        return any(abs(x - cx) <= threshold and abs(y - cy) <= threshold for cx, cy in coordinates_set)
    
    return all(is_nearby(coord, coordinates_set) for coord in bubbles)

def classify_coordinates(bubbles):
    """ Koordinatalarni `student_id`, `phone_number` yoki `bubbles` sifatida tasniflaydi. """
    student_id_coords, phone_number_coords, bubble_coords = [], [], []
    
    for x, y in bubbles:
        if 0.1 <= x <= 9.6:
            student_id_coords.append((x, y))
        elif 0.1 <= x <= 9.9:
            phone_number_coords.append((x, y))
        else:
            bubble_coords.append((x, y))
    
    return student_id_coords, phone_number_coords, bubble_coords

class ProcessImageView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        transaction_id = str(uuid.uuid4())[:8]
        try:
            csv_file = request.FILES.get('file')
            image_url = request.data.get('img_url')

            if not csv_file:
                logger.error("CSV fayl yuklanmagan")
                return Response({"error": "CSV fayl yuklanmagan"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                csv_data = csv_file.read().decode('utf-8')
                csv_io = StringIO(csv_data)
                reader = csv.DictReader(csv_io)
            except Exception as e:
                logger.error("CSV faylni o‘qishda xato: %s", str(e))
                return Response({"error": "CSV faylni o‘qishda xato"}, status=status.HTTP_400_BAD_REQUEST)

            bubbles = []
            for row in reader:
                try:
                    x = float(row.get('x_coord'))
                    y = float(row.get('y_coord'))
                    bubbles.append((x, y))
                except (ValueError, TypeError) as e:
                    logger.warning("Noto‘g‘ri koordinata: %s, Xato: %s", row, str(e))
                    continue

            logger.info("CSV fayldan %d ta koordinata yuklandi", len(bubbles))

            # Asosiy CSV fayldagi ma'lumotlarni yuklash va tekshirish
            coordinates_set = load_coordinates(COORDINATES_PATH)
            if not validate_coordinates(bubbles, coordinates_set):
                logger.error("CSV fayl noto‘g‘ri ma‘lumotlar o‘z ichiga olgan")
                return Response({"error": "CSV fayl noto‘g‘ri ma‘lumotlar o‘z ichiga olgan"}, status=status.HTTP_400_BAD_REQUEST)

            # Koordinatalarni tasniflash
            try:
                student_id_coords, phone_number_coords, bubble_coords = classify_coordinates(bubbles)
            except Exception as e:
                logger.error("Koordinatalarni tasniflashda xato: %s", str(e))
                return Response({"error": "Koordinatalarni tasniflashda xato"}, status=status.HTTP_400_BAD_REQUEST)

            if not student_id_coords:
                logger.error("Student ID aniqlanmadi")
                return Response({"error": "Student ID aniqlanmadi"}, status=status.HTTP_400_BAD_REQUEST)

            logger.info("Aniqlangan Student ID: %s", student_id_coords)

            with transaction.atomic():
                processed_test = ProcessedTest.objects.create(
                    student_id=student_id_coords,
                    phone_number=phone_number_coords,
                    bubbles=bubble_coords,
                    image_url=image_url
                )

            logger.info("Ma'lumotlar muvaffaqiyatli saqlandi. Transaction ID: %s", transaction_id)

            return Response({
                "message": "Ma'lumotlar saqlandi",
                "transaction_id": transaction_id,
                "details": {
                    "student_id": student_id_coords,
                    "phone_number": phone_number_coords,
                    "answers_count": len(bubble_coords)
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error("Server xatosi: %s", str(e))
            return Response({"error": "Ichki server xatosi"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

