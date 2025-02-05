import logging
import os
import json
from threading import Lock

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from conf.settings import BASE_DIR

logger = logging.getLogger(__name__)

# Global o'zgaruvchilar
SAVED_DATA = []  # Har bir element ro'yxat shaklida saqlanadi
SAVED_DATA_LOCK = Lock()

COORDINATES_PATH = os.path.join(BASE_DIR, 'app/coordinates/coordinates.json')
COORDINATES_CACHE = None
COORDINATES_LAST_MODIFIED = None
COORDINATES_CACHE_LOCK = Lock()


def load_coordinates():
    """
    JSON fayldan student va phone koordinatalarni yuklaydi.
    
    Agar fayl mavjud bo'lmasa yoki format xato bo'lsa, bo'sh lug'atlar qaytaradi.
    Cache mexanizmi yordamida fayl o'zgarmagan bo'lsa, avvalgi natijani qaytaradi.
    """
    global COORDINATES_CACHE, COORDINATES_LAST_MODIFIED

    if not os.path.exists(COORDINATES_PATH):
        logger.error("Coordinates JSON fayl topilmadi.")
        return {}, {}

    current_mtime = os.path.getmtime(COORDINATES_PATH)
    with COORDINATES_CACHE_LOCK:
        if COORDINATES_CACHE is not None and current_mtime == COORDINATES_LAST_MODIFIED:
            return COORDINATES_CACHE

        try:
            with open(COORDINATES_PATH, 'r', encoding='utf-8') as file:
                data = json.load(file)

            if not isinstance(data, dict):
                logger.error("JSON format noto‘g‘ri!")
                return {}, {}

            student_coords = data.get("student_coordinates", {})
            phone_coords = data.get("phone_coordinates", {})

            COORDINATES_CACHE = (student_coords, phone_coords)
            COORDINATES_LAST_MODIFIED = current_mtime
            return COORDINATES_CACHE

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode xatosi: {e}")
        except Exception as e:
            logger.error(f"Koordinatalarni yuklashda xatolik: {e}")

        return {}, {}


def match_coordinates(user_coords, saved_data, max_threshold=5):
    """
    Saqlangan koordinatalarni foydalanuvchi koordinatalari bilan solishtirib,
    ±max_threshold oralig‘ida mos keladigan koordinatalarni topadi.
    
    Natija sifatida lug'at (key: mos kelgan element identifikatori, value: ro'yxat)
    qaytaradi.
    """
    matches = {}
    if not saved_data:
        return matches

    for key, saved_list in saved_data.items():
        seen = set()
        for index, coord_dict in enumerate(saved_list):
            # Har bir element lug'at ko'rinishida bo'lib, bitta kalit-qiymat juftligini o'z ichiga oladi.
            for _, saved_coord in coord_dict.items():
                sx, sy = saved_coord.get("x"), saved_coord.get("y")
                if sx is None or sy is None:
                    continue

                for user_coord in user_coords:
                    ux, uy = user_coord.get("x"), user_coord.get("y")
                    if ux is None or uy is None:
                        continue

                    if (sx - max_threshold <= ux <= sx + max_threshold) and \
                       (sy - max_threshold <= uy <= sy + max_threshold):
                        coord_tuple = (sx, sy)
                        if coord_tuple not in seen:
                            seen.add(coord_tuple)
                            matches.setdefault(key, []).append({str(index): saved_coord})
                        # Agar moslik topilgan bo'lsa, shu user koordinata uchun boshqa tekshirishlar o'tkazilmaydi
                        break
    return matches


def find_matching_coordinates(user_coords, student_coords, phone_coords, max_threshold=5):
    """
    Foydalanuvchi koordinatalari bilan student va phone koordinatalarni taqqoslaydi.
    
    Natijada tuple (student_matches, phone_matches) shaklida lug'atlarni qaytaradi.
    """
    student_matches = match_coordinates(user_coords, student_coords, max_threshold)
    phone_matches = match_coordinates(user_coords, phone_coords, max_threshold)
    return student_matches, phone_matches


class ProcessImageView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """Saqlangan barcha ma'lumotlarni qaytaradi."""
        with SAVED_DATA_LOCK:
            # Natijani dict ichida qaytarishimiz mumkin, ammo SAVED_DATA ning o'zi ro'yxatdir
            return Response({"saved_data": SAVED_DATA}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """
        Kelayotgan so'rovdan image_url va koordinatalarni qabul qiladi,
        ularni saqlangan koordinatalar bilan solishtirib, mos keladigan natijalarni qaytaradi.
        Agar mos keladigan natijalar bo'lsa, ularni global SAVED_DATA ro'yxatiga qo'shadi.
        """
        try:
            image_url = request.data.get('image_url')
            user_coords = request.data.get('coordinates', [])

            if not image_url or not isinstance(user_coords, list):
                return Response(
                    {"error": "Both 'image_url' and 'coordinates' (list formatida) majburiy."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Faqat to'g'ri formatdagi koordinatalarni qabul qilamiz
            valid_user_coords = [
                coord for coord in user_coords
                if isinstance(coord, dict) and "x" in coord and "y" in coord
            ]
            if not valid_user_coords:
                return Response(
                    {"error": "Yaroqsiz yoki bo'sh koordinatalar kiritildi."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            student_coords, phone_coords = load_coordinates()

            student_matches, phone_matches = find_matching_coordinates(valid_user_coords, student_coords, phone_coords)

            # Endi ma'lumotlarni ro'yxat shaklida saqlaymiz:
            # [image_url, user_coordinates, matching_coordinates, phone_number_matches]
            saved_entry = [
                image_url,
                valid_user_coords,
                student_matches,
                phone_matches
            ]

            if student_matches or phone_matches:
                with SAVED_DATA_LOCK:
                    SAVED_DATA.append(saved_entry)

            response_data = {
                "image_url": image_url,
                "user_coordinates": valid_user_coords,
                "matching_coordinates": student_matches,
                "phone_number_matches": phone_matches
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Xatolik: {e}", exc_info=True)
            return Response(
                {"error": f"Xatolik yuz berdi: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request, *args, **kwargs):
        """Barcha saqlangan ma'lumotlarni o'chiradi."""
        with SAVED_DATA_LOCK:
            SAVED_DATA.clear()
        return Response(
            {"message": "Barcha ma'lumotlar o‘chirildi."},
            status=status.HTTP_200_OK
        )
