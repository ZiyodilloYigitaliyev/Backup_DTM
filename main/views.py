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
PHONE_COORDINATES_PATH = os.path.join(BASE_DIR, 'app/coordinates/phone_number.json')
ANSWER_COORDINATES_PATH = os.path.join(BASE_DIR, 'app/coordinates/answer_coordinates.json')  # Yangi path

COORDINATES_CACHE = None
COORDINATES_LAST_MODIFIED = None
PHONE_COORDINATES_CACHE = None
PHONE_COORDINATES_LAST_MODIFIED = None
ANSWER_COORDINATES_CACHE = None
ANSWER_COORDINATES_LAST_MODIFIED = None

COORDINATES_CACHE_LOCK = Lock()
PHONE_COORDINATES_CACHE_LOCK = Lock()
ANSWER_COORDINATES_CACHE_LOCK = Lock()


def load_coordinates(file_path, cache, last_modified, cache_lock):
    """JSON fayldan koordinatalarni yuklash."""
    if not os.path.exists(file_path):
        logger.error(f"JSON fayl topilmadi: {file_path}")
        return {}

    current_mtime = os.path.getmtime(file_path)

    with cache_lock:
        if cache is not None and current_mtime == last_modified:
            return cache

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

                if not isinstance(data, dict) or "coordinates" not in data:
                    logger.error(f"JSON format noto‘g‘ri yoki 'coordinates' kaliti mavjud emas: {file_path}")
                    return {}

                coordinates = data["coordinates"]

                if not isinstance(coordinates, (list, dict)):  # List yoki dict bo‘lishi kerak
                    logger.error(f"Koordinatalar noto‘g‘ri shaklda: {file_path}")
                    return {}

                cache = coordinates
                last_modified = current_mtime
                return cache

        except json.JSONDecodeError:
            logger.error(f"JSON faylni o'qishda xatolik yuz berdi: {file_path}")
            return {}
        except Exception as e:
            logger.error(f"Xatolik yuz berdi: {e}")
            return {}


def find_matching_coordinates(user_coordinates, saved_coordinates, max_threshold=5):
    """Koordinatalarni taqqoslab, o'xshashlarini qaytaradi."""
    matching = {}

    if isinstance(saved_coordinates, dict):  # Agar `saved_coordinates` dictionary bo‘lsa
        for key, answers in saved_coordinates.items():  # "1", "2", "3", ...
            for sub_key, coord_list in answers.items():  # "A", "B", "C", "D"
                sx, sy = coord_list[0], coord_list[1]  # X va Y koordinatalarni ajratib olish

                for user_coord in user_coordinates:
                    ux, uy = user_coord["x"], user_coord["y"]

                    if (sx - max_threshold <= ux <= sx + max_threshold) and (sy - max_threshold <= uy <= sy + max_threshold):
                        if key not in matching:
                            matching[key] = []
                        matching[key].append({sub_key: {"x": sx, "y": sy}})  # O‘xshash topilgan koordinata
    else:
        for key, saved_list in saved_coordinates[0].items():
            seen_coords = set()

            for index, indexed_coord in enumerate(saved_list):
                for _, saved_coord in indexed_coord.items():
                    sx, sy = saved_coord["x"], saved_coord["y"]

                    for user_coord in user_coordinates:
                        ux, uy = user_coord["x"], user_coord["y"]

                        if (sx - max_threshold <= ux <= sx + max_threshold) and (sy - max_threshold <= uy <= sy + max_threshold):
                            coord_tuple = (sx, sy)

                            if coord_tuple not in seen_coords:
                                seen_coords.add(coord_tuple)

                                if key not in matching:
                                    matching[key] = []
                                matching[key].append({str(index): saved_coord})

    return matching


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

            saved_coords = load_coordinates(COORDINATES_PATH, COORDINATES_CACHE, COORDINATES_LAST_MODIFIED, COORDINATES_CACHE_LOCK)
            phone_coords = load_coordinates(PHONE_COORDINATES_PATH, PHONE_COORDINATES_CACHE, PHONE_COORDINATES_LAST_MODIFIED, PHONE_COORDINATES_CACHE_LOCK)
            answer_coords = load_coordinates(ANSWER_COORDINATES_PATH, ANSWER_COORDINATES_CACHE, ANSWER_COORDINATES_LAST_MODIFIED, ANSWER_COORDINATES_CACHE_LOCK)  # Yangi fileni yuklaymiz

            matches = find_matching_coordinates(valid_user_coords, saved_coords)
            phone_matches = find_matching_coordinates(valid_user_coords, phone_coords)
            answer_matches = find_matching_coordinates(valid_user_coords, answer_coords)  # Yangi fayl uchun taqqoslash

            data = {
                "image_url": image_url,
                "user_coordinates": user_coords,
                "matching_coordinates": matches,
                "phone_coordinates": phone_matches,  # Phone koordinatalarni ham qaytaramiz
                "answer_coordinates": answer_matches  # Yangi fayldan topilgan koordinatalar
            }

            if matches or phone_matches or answer_matches:
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
