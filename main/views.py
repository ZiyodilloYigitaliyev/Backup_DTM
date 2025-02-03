import os
import csv
import traceback
import uuid
import json
import logging
from io import StringIO
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .models import ProcessedTest, ProcessedTestResult

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COORDINATES_PATH = os.path.join(BASE_DIR, 'app/coordinates/coordinates.csv')
ID_PATH = os.path.join(BASE_DIR, 'app/coordinates/coordinates.csv')
PHONE_NUMBER_PATH = os.path.join(BASE_DIR, 'app/coordinates/coordinates.csv')


def extract_from_coordinates(bubbles, coordinates_dict):
    """Koordinatalarni tekshirish va log qilish.
    
    bubbles – foydalanuvchi yuborgan koordinatalar (ro'yxat shaklida, masalan, [(x, y), ...])
    coordinates_dict – CSV dan yuklangan {key: [(x, y), ...]} shaklidagi ma'lumotlar.
    
    Agar bubbles ichida coordinates_dict dan biror koordinata mos kelsa, {key: coord} lug'atini qaytaradi.
    """
    logger.info(
        "Koordinatalarni ajratish boshlandi. Bubbles soni: %d, Koordinatalar to'plami: %s", 
        len(bubbles), list(coordinates_dict.keys())
    )
    
    if not bubbles:
        logger.error("Bubbles bo'sh! Ajratib bo'lmaydi.")
        return None
        
    if not coordinates_dict:
        logger.error("Koordinatalar bo'sh! Ajratib bo'lmaydi.")
        return None

    logger.debug("Har bir koordinata to'plami uchun tekshirish:")
    for key, coord_list in coordinates_dict.items():
        logger.debug("%s uchun %d ta koordinata tekshirilmoqda...", key, len(coord_list))
        for idx, coord in enumerate(coord_list, 1):
            logger.debug("Tekshirilayotgan koordinata [%d/%d]: %s", idx, len(coord_list), coord)
            if coord in bubbles:
                logger.info("Topildi: %s - %s", key, coord)
                return {key: coord}

    logger.warning("Hech qanday moslik topilmadi!")
    return None


def load_coordinates_from_csv(csv_path):
    """CSV fayllarni yuklash va loglarni batafsil yuritish.
    
    CSV faylning birinchi ustuni kalit (key) bo‘lib, qolgan ustunlar ketma-ket
    x_coord, y_coord juftliklari shaklida keltirilishi kerak.
    """
    logger.info("➤ CSV yuklash boshlandi: %s", csv_path)
    data = {}
    try:
        with open(csv_path, 'r') as file:
            reader = csv.reader(file)
            headers = next(reader)  # bosh satrni o'qib chiqamiz
            for row in reader:
                if not row:
                    continue
                key = row[0]
                try:
                    coordinates = [(int(row[i]), int(row[i+1])) for i in range(1, len(row), 2)]
                except (ValueError, IndexError) as ve:
                    logger.error("Koordinatalarni o'qishda xato: %s", str(ve))
                    continue
                data[key] = coordinates
            logger.info("✓ CSV muvaffaqiyatli yuklandi. Elementlar soni: %d", len(data))
            logger.debug("Namuna ma'lumot: %s", str(data)[:100])
            return data
    except FileNotFoundError:
        logger.critical("⚠️ File topilmadi: %s", csv_path, exc_info=True)
        raise
    except Exception as e:
        logger.critical("⚠️ Noma'lum xato: %s", str(e), exc_info=True)
        raise


class ProcessImageView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        transaction_id = str(uuid.uuid4())[:8]  # Unique transaction ID
        logger.info("⎈⎈⎈ Yangi so'rov qabul qilindi ⎈⎈⎈ | Transaction ID: %s", transaction_id)

        try:
            # CSV faylni qabul qilish
            csv_file = request.FILES.get('file')
            file_url = request.POST.get('file_url')  # Agar file_url ham yuborilsa
            if not csv_file:
                logger.error("✖︎ CSV fayl topilmadi!", extra={'transaction_id': transaction_id})
                return Response(
                    {"error": "CSV fayl yuborilmagan"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # CSV faylni o'qish
            try:
                csv_data = csv_file.read().decode('utf-8')
            except Exception as e:
                logger.error("CSV fayl dekodlashda xato: %s", str(e))
                return Response(
                    {"error": "CSV faylni o'qishda xato"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            csv_io = StringIO(csv_data)
            reader = csv.DictReader(csv_io)

            # CSV fayl ichidan ma'lumotlarni chiqarib olish
            bubbles = []        # bubbles: list of (x, y)
            phone_number = None
            extracted_student_id = None
            marked_answers = {}  # {question: answer}

            for row in reader:
                data_type = row.get('data_type', '').strip().lower()
                if data_type == 'bubble':
                    try:
                        x = int(row.get('x_coord'))
                        y = int(row.get('y_coord'))
                        bubbles.append((x, y))
                    except Exception as e:
                        logger.error("Bubble koordinatalarini o'qishda xato: %s", str(e))
                        continue
                elif data_type == 'phone_number':
                    phone_number = row.get('value', '').strip()
                elif data_type == 'student_id':
                    extracted_student_id = row.get('value', '').strip()
                elif data_type == 'answer':
                    question = row.get('question', '').strip()
                    answer = row.get('value', '').strip()
                    if question:
                        marked_answers[question] = answer

            logger.info("CSV fayldan olingan bubbles: %s", bubbles)
            logger.info("CSV fayldan olingan telefon raqam: %s", phone_number or "Topilmadi")
            logger.info("CSV fayldan olingan student ID: %s", extracted_student_id or "Topilmadi")
            logger.info("CSV fayldan olingan javoblar: %s", json.dumps(marked_answers, ensure_ascii=False))

            if not extracted_student_id:
                logger.error("✖︎ Student ID topilmadi!", extra={'transaction_id': transaction_id})
                return Response(
                    {"error": "Student ID aniqlanmadi"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Javoblarni tekshirish (Backup app ichidagi true_answer bilan taqqoslash)
            logger.info("⎇ Test javoblarini qidirish...")
            question_coords = load_coordinates_from_csv(COORDINATES_PATH)
            # extract_from_coordinates funksiyasi faqat bitta mos keluvchi koordinatani qaytaradi.
            # Agar kerak bo'lsa, uni moslashtirish mumkin, lekin vazifa o'zgarmaydi.
            extracted_answers = extract_from_coordinates(bubbles, question_coords)
            if extracted_answers:
                logger.info("📝 Javoblar natijasi: %s", json.dumps(extracted_answers, indent=2))
            else:
                logger.info("📝 Javoblar topilmadi")

            # Ma'lumotlar bazasiga yozish
            logger.info("💾 Ma'lumotlar bazasiga yozish boshlandi...")
            with transaction.atomic():
                processed_test = ProcessedTest.objects.create(
                    file_url=file_url if file_url else "",
                    phone_number=phone_number,
                    bubbles=bubbles  # Eslatma: bubbles JSONField bo‘lsa, ro‘yxat (yoki list of lists) shaklida saqlash tavsiya etiladi.
                )
                logger.info("✓ ProcessedTest yaratildi | ID: %s", processed_test.id)

                if marked_answers:
                    for q, a in marked_answers.items():
                        ProcessedTestResult.objects.create(
                            student=processed_test,
                            student_answer=json.dumps({q: a}),
                            is_correct=True,  # Bu yerda javob to'g'ri deb belgilandi; kerak bo'lsa, solishtirish algoritmini qo'shing.
                            score=1
                        )
                        logger.debug("✓ Javob saqlandi: Savol-%s ➔ %s", q, a)
                else:
                    logger.warning("⚠️ Saqlanadigan javoblar yo'q!")

            logger.info("✅ So'rov muvaffaqiyatli yakunlandi!")
            return Response({
                "message": "Ma'lumotlar saqlandi",
                "transaction_id": transaction_id,
                "details": {
                    "extracted_student_id": extracted_student_id,
                    "db_student_id": processed_test.student_id,
                    "phone_number": phone_number,
                    "answers_count": len(marked_answers)
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.critical("‼️‼️ Kritik xato ‼️‼️ | Transaction ID: %s | Xato: %s", 
                            transaction_id, str(e), exc_info=True)
            logger.debug("Xato tafsilotlari: %s", traceback.format_exc())
            return Response(
                {"error": "Server xatosi", "transaction_id": transaction_id},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
