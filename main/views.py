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
PHONE_COORDINATES_PATH = os.path.join(BASE_DIR, 'app/coordinates/phone_number.json')  # Agar kerak bo'lsa

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

            # Agar malumotlar lug'at shaklida bo'lmasa, bo'sh lug'atga aylantiramiz.
            if not isinstance(student_coords, dict):
                student_coords = {}
            if not isinstance(phone_coords, dict):
                phone_coords = {}

            COORDINATES_CACHE = (student_coords, phone_coords)
            COORDINATES_LAST_MODIFIED = current_mtime
            return COORDINATES_CACHE

        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"JSON yuklashda xatolik: {e}")
            return {}, {}


def match_coordinates(user_coords, saved_data, max_threshold=5):
    """
    Saqlangan koordinatalarni foydalanuvchi koordinatalari bilan solishtirib,
    ±max_threshold oralig‘ida mos keladigan koordinatalarni indeks bilan qaytaradi.
    """
    matches = {}
    if not saved_data:
        return matches

    for key, saved_list in saved_data.items():
        seen = set()
        for index, coord_dict in enumerate(saved_list):
            # Har bir element lug'at shaklida bo'lib, bitta kalit-qiymat juftligini o'z ichiga oladi.
            for _, saved_coord in coord_dict.items():
                sx, sy = saved_coord.get("x"), saved_coord.get("y")
                if sx is None or sy is None:
                    continue
                for user_coord in user_coords:
                    ux, uy = user_coord.get("x"), user_coord.get("y")
                    if ux is None or uy is None:
                        continue
                    if (sx - max_threshold <= ux <= sx + max_threshold) and (sy - max_threshold <= uy <= sy + max_threshold):
                        coord_tuple = (sx, sy)
                        if coord_tuple not in seen:
                            seen.add(coord_tuple)
                            matches.setdefault(key, []).append({str(index): saved_coord})
                        break
    return matches


def find_matching_coordinates(user_coords, student_coords, phone_coords, max_threshold=5):
    """
    Foydalanuvchi koordinatalarini student va phone koordinatalar bilan solishtiradi.
    Natija sifatida ikkita alohida lug'at qaytaradi:
      - student_matches: Student ID uchun mos kelgan koordinatalar.
      - phone_matches: Telefon raqami uchun mos kelgan koordinatalar.
    """
    student_matches = match_coordinates(user_coords, student_coords, max_threshold)
    phone_matches = match_coordinates(user_coords, phone_coords, max_threshold)
    return student_matches, phone_matches


class ProcessImageView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        with SAVED_DATA_LOCK:
            return Response({"saved_data": SAVED_DATA}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        try:
            image_url = request.data.get('image_url')
            user_coords = request.data.get('coordinates', [])

            if not image_url or not isinstance(user_coords, list):
                return Response(
                    {"error": "image_url va coordinates (list formatida) majburiy"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            valid_user_coords = [
                coord for coord in user_coords if isinstance(coord, dict) and "x" in coord and "y" in coord
            ]
            if not valid_user_coords:
                return Response(
                    {"error": "Yaroqsiz yoki bo'sh koordinatalar kiritildi."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            student_coords, phone_coords = load_coordinates()

            student_matches, phone_matches = find_matching_coordinates(valid_user_coords, student_coords, phone_coords)

            data = {
                "image_url": image_url,
                "user_coordinates": user_coords,
                "matching_coordinates": student_matches,
                "phone_number_matches": phone_matches
            }

            with SAVED_DATA_LOCK:
                SAVED_DATA.append(data)

            return Response(data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Xatolik: {e}", exc_info=True)
            return Response(
                {"error": f"Xatolik yuz berdi: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request, *args, **kwargs):
        with SAVED_DATA_LOCK:
            SAVED_DATA.clear()
        return Response(
            {"message": "Barcha ma'lumotlar o‘chirildi."},
            status=status.HTTP_200_OK
        )
