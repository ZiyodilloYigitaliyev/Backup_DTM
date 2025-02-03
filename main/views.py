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
# Student ID uchun alohida CSV fayl (masalan, 'student_id.csv')
STUDENT_COORDINATES_PATH = os.path.join(BASE_DIR, 'app/coordinates/coordinates.csv')
# Phone Number uchun alohida CSV fayl (masalan, 'phone_number.csv')
PHONE_COORDINATES_PATH = os.path.join(BASE_DIR, 'app/coordinates/phone_number.csv')

def load_coordinates(csv_path):
    """
    CSV faylni yuklab, koordinatalarni (x, y) juftliklari sifatida to'plamga joylaydi.
    """
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

def validate_coordinates(bubbles, coordinates_set, threshold=6):
    """
    Kiritilgan koordinatalarni CSV faylidagi ma'lumotlar bilan solishtiradi.
    Har bir koordinata, CSV fayldagi qaysidir koordinata bilan threshold oralig'ida bo'lsa,
    mos deb hisoblanadi.
    """
    def is_nearby(coord, coordinates_set):
        x, y = coord
        return any(abs(x - cx) <= threshold and abs(y - cy) <= threshold for cx, cy in coordinates_set)
    
    return all(is_nearby(coord, coordinates_set) for coord in bubbles)

def classify_coordinates(bubbles):
    """
    Kiritilgan koordinatalarni ro'yxat tartibiga asoslanib tasniflaydi.
    
    Misol uchun:
      - Birinchi 2 ta koordinata student_id uchun,
      - Keyingi 7 ta koordinata phone_number uchun,
      - Qolganlari bubble (javob) koordinatalari sifatida qabul qilinadi.
    
    (Indeks oralig'ini o'zingizning talablaringizga moslab o'zgartiring.)
    """
    student_id_coords = bubbles[:2]
    phone_number_coords = bubbles[2:9]
    bubble_coords = bubbles[9:]
    
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
                    # Avval float qiymatlarni int ga o'zgartirayotganimizni ta'minlash
                    x = int(float(row.get('x_coord')))  # float dan int ga o'zgartirish
                    y = int(float(row.get('y_coord')))  # float dan int ga o'zgartirish
                    bubbles.append((x, y))
                except (ValueError, TypeError) as e:
                    logger.warning("Noto‘g‘ri koordinata: %s, Xato: %s", row, str(e))
                    continue

            logger.info("CSV fayldan %d ta koordinata yuklandi", len(bubbles))

            # Asosiy CSV fayldagi (barcha) koordinatalarni validatsiya qilish
            # (agar kerak bo'lsa; bu yerda butun fayl uchun umumiy validatsiyani amalga oshiramiz)
            all_coordinates_set = load_coordinates(STUDENT_COORDINATES_PATH)  # yoki boshqa mos CSV
            if not validate_coordinates(bubbles, all_coordinates_set):
                logger.error("CSV fayl noto‘g‘ri ma‘lumotlar o‘z ichiga olgan")
                return Response({"error": "CSV fayl noto‘g‘ri ma‘lumotlar o‘z ichiga olgan"}, status=status.HTTP_400_BAD_REQUEST)

            # Koordinatalarni tasniflash (indeks bo'yicha ajratish)
            try:
                student_id_coords, phone_number_coords, bubble_coords = classify_coordinates(bubbles)
            except Exception as e:
                logger.error("Koordinatalarni tasniflashda xato: %s", str(e))
                return Response({"error": "Koordinatalarni tasniflashda xato"}, status=status.HTTP_400_BAD_REQUEST)

            # Student ID koordinatalarini alohida CSV fayldagi ma'lumotlar bilan tekshirish
            student_coordinates_set = load_coordinates(STUDENT_COORDINATES_PATH)
            if not validate_coordinates(student_id_coords, student_coordinates_set):
                logger.error("Student ID koordinatalari CSV faylidagi ma'lumotlarga mos kelmadi")
                return Response({"error": "Student ID koordinatalari noto‘g‘ri"}, status=status.HTTP_400_BAD_REQUEST)

            # Phone Number koordinatalarini alohida CSV fayldagi ma'lumotlar bilan tekshirish
            phone_coordinates_set = load_coordinates(PHONE_COORDINATES_PATH)
            if not validate_coordinates(phone_number_coords, phone_coordinates_set):
                logger.error("Phone Number koordinatalari CSV faylidagi ma'lumotlarga mos kelmadi")
                return Response({"error": "Phone Number koordinatalari noto‘g‘ri"}, status=status.HTTP_400_BAD_REQUEST)

            if not student_id_coords:
                logger.error("Student ID aniqlanmadi")
                return Response({"error": "Student ID aniqlanmadi"}, status=status.HTTP_400_BAD_REQUEST)

            logger.info("Aniqlangan Student ID: %s", student_id_coords)
            logger.info("Aniqlangan Phone Number: %s", phone_number_coords)

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
