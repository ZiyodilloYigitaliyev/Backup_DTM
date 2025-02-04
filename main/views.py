import csv
import io
import uuid
import logging
from django.http import JsonResponse
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
    Har bir koordinata, CSV fayldagi qaysidir koordinata bilan threshold oralig'ida bo'lsa,
    mos deb hisoblanadi.
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

        # CSV faylni olish
        csv_file = request.FILES.get('file')
        if not csv_file:
            logger.error("CSV fayl yuklanmagan")
            return Response({"error": "CSV fayl yuklanmagan"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            csv_data = csv_file.read().decode('utf-8')
            csv_io = io.StringIO(csv_data)
            reader = csv.reader(csv_io)
            next(reader, None)  # Sarlavhani o'tkazib yuborish
        except Exception as e:
            logger.error("CSV faylni o‘qishda xato: %s", str(e))
            return Response({"error": "CSV faylni o‘qishda xato"}, status=status.HTTP_400_BAD_REQUEST)

        coordinates_set = set()
        for row in reader:
            if len(row) < 2:
                continue
            try:
                x, y = row[0].strip(), row[1].strip()
                if x and y:
                    coordinates_set.add((int(x), int(y)))
            except ValueError:
                logger.warning("Noto‘g‘ri koordinata: %s", row)
                continue

        logger.info("CSV fayldan %d ta koordinata yuklandi", len(coordinates_set))

        # Asosiy CSV fayldagi koordinatalarni yuklash
        all_coordinates_set = load_coordinates(STUDENT_COORDINATES_PATH)

        if not validate_coordinates(coordinates_set, all_coordinates_set):
            logger.error("CSV fayl noto‘g‘ri ma‘lumotlar o‘z ichiga olgan")
            return Response({"error": "CSV fayl noto‘g‘ri ma‘lumotlar o‘z ichiga olgan"}, status=status.HTTP_400_BAD_REQUEST)

        # Koordinatalarni tasniflash
        student_id_coords, phone_number_coords, bubble_coords = classify_coordinates(coordinates_set)
        

        # Student ID koordinatalarini tekshirish
        student_coordinates_set = load_coordinates(STUDENT_COORDINATES_PATH)
        if not validate_coordinates(student_id_coords, student_coordinates_set):
            logger.error("Student ID koordinatalari CSV faylidagi ma'lumotlarga mos kelmadi")
            return Response({"error": "Student ID koordinatalari noto‘g‘ri"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "transaction_id": transaction_id,
            "student_id_coords": student_id_coords,
            "phone_number_coords": phone_number_coords,
            "bubble_coords": bubble_coords,
            "status": "success"
        }, status=status.HTTP_200_OK)
