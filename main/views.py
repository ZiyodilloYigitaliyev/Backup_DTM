import json
import logging
import os
from threading import Lock
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from conf.settings import BASE_DIR

logger = logging.getLogger(__name__)

# Global o'zgaruvchilar va ularga qulf
SAVED_DATA = []
SAVED_DATA_LOCK = Lock()

COORDINATES_PATH = os.path.join(BASE_DIR, 'app/coordinates/coordinates.json')
COORDINATES_CACHE = None
COORDINATES_LAST_MODIFIED = None
COORDINATES_CACHE_LOCK = Lock()


def load_coordinates():
    """
    JSON fayldan koordinatalarni yuklash (student ID va phone number uchun).
    Agar fayl o'zgarmagan bo'lsa, keshlangan (cache) ma'lumot qaytariladi.
    
    Returns:
        tuple: (student_coordinates: dict, phone_coordinates: dict)
    """
    global COORDINATES_CACHE, COORDINATES_LAST_MODIFIED

    if not os.path.exists(COORDINATES_PATH):
        logger.error("JSON fayl topilmadi: %s", COORDINATES_PATH)
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
            logger.error("JSON yuklashda xatolik: %s", e)
            return {}, {}
        except Exception as e:
            logger.error("Kutilmagan xatolik JSONni yuklashda: %s", e)
            return {}, {}


def find_matching_coordinates(user_coordinates, student_coords, phone_coords, max_threshold=5):
    """
    Foydalanuvchi kiritgan koordinatalarni, student va telefon koordinatalari bilan solishtiradi.
    Koordinatalar ±max_threshold oralig'ida mos kelsa, ularni indekslari bilan qaytaradi.

    Args:
        user_coordinates (list): Foydalanuvchi kiritgan koordinatalar (dict lardan iborat, har biri "x" va "y" kalitlarga ega)
        student_coords (dict): Student koordinatalari
        phone_coords (dict): Telefon koordinatalari
        max_threshold (int, optional): Tekshirish oralig'i. Default 5.

    Returns:
        tuple: (matching_student_coordinates, matching_phone_coordinates)
    """

    def match_coordinates(user_coords, saved_data, threshold):
        matching = {}

        if not saved_data:
            return matching

        # Foydalanuvchi koordinatalarni oldindan tuple shaklida ajratib olish
        user_tuples = [
            (coord.get("x"), coord.get("y"))
            for coord in user_coords
            if isinstance(coord, dict) and "x" in coord and "y" in coord
        ]

        for key, saved_list in saved_data.items():
            seen_coords = set()

            for index, indexed_coord in enumerate(saved_list):
                # indexed_coord taxminan bitta elementli dict bo'lishi kutilmoqda
                for saved_coord in indexed_coord.values():
                    sx = saved_coord.get("x")
                    sy = saved_coord.get("y")
                    if sx is None or sy is None:
                        continue

                    for ux, uy in user_tuples:
                        if (sx - threshold <= ux <= sx + threshold) and (sy - threshold <= uy <= sy + threshold):
                            coord_tuple = (sx, sy)
                            if coord_tuple not in seen_coords:
                                seen_coords.add(coord_tuple)
                                matching.setdefault(key, []).append({str(index): saved_coord})
                            # Agar birinchi moslik topilgan bo'lsa, qo'shimcha tekshirishga hojat yo'q
                            break

        return matching

    matching_student = match_coordinates(user_coordinates, student_coords, max_threshold)
    matching_phone = match_coordinates(user_coordinates, phone_coords, max_threshold)
    return matching_student, matching_phone


class ProcessImageView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """
        Saqlangan ma'lumotlarni ko'rsatadi.
        """
        with SAVED_DATA_LOCK:
            return Response({"saved_data": SAVED_DATA}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """
        Tasvir URL va foydalanuvchi kiritgan koordinatalarni qabul qilib,
        ularni student va telefon koordinatalari bilan solishtiradi.
        Mos kelsa, ma'lumotni saqlaydi va natijani qaytaradi.
        """
        try:
            image_url = request.data.get('image_url')
            user_coords = request.data.get('coordinates', [])

            if not image_url or not isinstance(user_coords, list):
                return Response(
                    {"error": "image_url va coordinates (list formatida) majburiy"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Faqat "x" va "y" mavjud bo'lgan koordinatalarni qabul qilamiz
            valid_user_coords = [
                coord for coord in user_coords
                if isinstance(coord, dict) and "x" in coord and "y" in coord
            ]

            student_coords, phone_coords = load_coordinates()

            matching_student, matching_phone = find_matching_coordinates(
                valid_user_coords, student_coords, phone_coords
            )

            response_data = {
                "image_url": image_url,
                "user_coordinates": valid_user_coords,
                "matching_coordinates": matching_student,
                "phone_number_matches": matching_phone
            }

            # Agar mosliklar mavjud bo'lsa, ma'lumotlarni saqlaymiz
            if matching_student or matching_phone:
                with SAVED_DATA_LOCK:
                    SAVED_DATA.append(response_data)

            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error("Xatolik: %s", e, exc_info=True)
            return Response(
                {"error": f"Xatolik yuz berdi: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request, *args, **kwargs):
        """
        Saqlangan barcha ma'lumotlarni tozalaydi.
        """
        with SAVED_DATA_LOCK:
            SAVED_DATA.clear()
        return Response(
            {"message": "Barcha ma'lumotlar o‘chirildi"},
            status=status.HTTP_200_OK
        )
