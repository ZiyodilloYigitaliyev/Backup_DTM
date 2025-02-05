import logging
import os
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from conf.settings import BASE_DIR
from threading import Lock

logger = logging.getLogger(__name__)

SAVED_DATA = []
SAVED_DATA_LOCK = Lock()

COORDINATES_PATH = os.path.join(BASE_DIR, 'app/coordinates/coordinates.json')

COORDINATES_CACHE = None
COORDINATES_LAST_MODIFIED = None
COORDINATES_CACHE_LOCK = Lock()


def load_coordinates():
    """JSON fayldan koordinatalarni yuklash (student ID va phone number uchun)."""
    global COORDINATES_CACHE, COORDINATES_LAST_MODIFIED

    if not os.path.exists(COORDINATES_PATH):
        logger.error("JSON fayl topilmadi.")
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
                return student_coords, phone_coords

        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"JSON yuklashda xatolik: {e}")
            return {}, {}


def find_matching_coordinates(user_coordinates, student_coords, phone_coords, max_threshold=5):
    """Foydalanuvchi koordinatalarini ±5 oralig‘ida tekshiradi va indeks bilan qaytaradi."""
    
    def match_coordinates(user_coords, saved_data):
        """Barcha turdagi koordinatalar uchun umumiy funksiya."""
        matching = {}

        if saved_data:
            for key, saved_list in saved_data.items():
                seen_coords = set()

                for index, indexed_coord in enumerate(saved_list):
                    for _, saved_coord in indexed_coord.items():
                        sx, sy = saved_coord["x"], saved_coord["y"]

                        for user_coord in user_coords:
                            ux, uy = user_coord["x"], user_coord["y"]

                            if (sx - max_threshold <= ux <= sx + max_threshold) and (sy - max_threshold <= uy <= sy + max_threshold):
                                coord_tuple = (sx, sy)

                                if coord_tuple not in seen_coords:
                                    seen_coords.add(coord_tuple)

                                    if key not in matching:
                                        matching[key] = []
                                    matching[key].append({str(index): saved_coord})

        return matching

    return match_coordinates(user_coordinates, student_coords), match_coordinates(user_coordinates, phone_coords)


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

            student_coords, phone_coords = load_coordinates()

            # **O‘xshash koordinatalarni topish**
            matching_coordinates, phone_number_matches = find_matching_coordinates(valid_user_coords, student_coords, phone_coords)

            data = {
                "image_url": image_url,
                "user_coordinates": user_coords,
                "matching_coordinates": matching_coordinates,
                "phone_number_matches": phone_number_matches
            }

            if matching_coordinates or phone_number_matches:
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
            {"message": "Barcha ma'lumotlar o‘chirildi"},
            status=status.HTTP_200_OK
        )
