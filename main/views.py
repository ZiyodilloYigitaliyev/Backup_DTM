import logging
import os
import json
from threading import Lock
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from conf.settings import BASE_DIR

logger = logging.getLogger(__name__)

# Global o'zgaruvchilar va qulflar
SAVED_DATA = []
SAVED_DATA_LOCK = Lock()

COORDINATES_PATH = os.path.join(BASE_DIR, 'app/coordinates/coordinates.json')
COORDINATES_CACHE = None
COORDINATES_LAST_MODIFIED = None
COORDINATES_CACHE_LOCK = Lock()


def load_coordinates():
    """JSON fayldan koordinatalarni yuklab, strukturani tekshiradi va cache qiladi."""
    global COORDINATES_CACHE, COORDINATES_LAST_MODIFIED

    if not os.path.exists(COORDINATES_PATH):
        logger.error(f"Fayl topilmadi: {COORDINATES_PATH}")
        return {}, {}

    current_mtime = os.path.getmtime(COORDINATES_PATH)
    with COORDINATES_CACHE_LOCK:
        if COORDINATES_CACHE and current_mtime == COORDINATES_LAST_MODIFIED:
            return COORDINATES_CACHE

        try:
            with open(COORDINATES_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Struktura tekshiruvi
            if not all(key in data for key in ("student_coordinates", "phone_coordinates")):
                raise ValueError("JSON faylda kerakli kalitlar yo'q")

            student_coords = data["student_coordinates"]
            phone_coords = data["phone_coordinates"]

            # Ma'lumotlar strukturasi tekshiruvi
            if not all(isinstance(d, dict) for d in (student_coords, phone_coords)):
                raise TypeError("Koordinatalar noto'g'ri formatda")

            COORDINATES_CACHE = (student_coords, phone_coords)
            COORDINATES_LAST_MODIFIED = current_mtime
            logger.info("Koordinatalar muvaffaqiyatli yangilandi")
            return COORDINATES_CACHE

        except Exception as e:
            logger.error(f"Xatolik: {str(e)}", exc_info=True)
            return {}, {}


def validate_coordinate(coord):
    """Koordinata strukturasi va qiymatlarini tekshiradi"""
    if not isinstance(coord, dict):
        return False
    if "x" not in coord or "y" not in coord:
        return False
    if not (isinstance(coord["x"], (int, float)) and isinstance(coord["y"], (int, float))):
        return False
    return True


def match_coordinates(user_coords, saved_data, max_threshold=5):
    """Koordinatalarni solishtirishni optimallashtirilgan versiyasi"""
    matches = {}
    if not saved_data or not user_coords:
        return matches

    for key, items in saved_data.items():
        matched_items = []
        for idx, item in enumerate(items):
            for item_key, saved_coord in item.items():
                if not validate_coordinate(saved_coord):
                    logger.warning(f"Yaroqsiz koordinata: {key}[{idx}]")
                    continue
                
                sx = saved_coord["x"]
                sy = saved_coord["y"]
                
                for user_coord in user_coords:
                    if not validate_coordinate(user_coord):
                        continue
                    
                    ux = user_coord["x"]
                    uy = user_coord["y"]
                    
                    if (abs(sx - ux) <= max_threshold) and (abs(sy - uy) <= max_threshold):
                        matched_items.append({item_key: saved_coord})
                        break  # Birorta moslik topilsa keyingisiga o'tmaymiz

        if matched_items:
            matches[key] = matched_items

    return matches


class ProcessImageView(APIView):
    permission_classes = [AllowAny]
    MAX_THRESHOLD = 5  # Konfiguratsiya uchun

    def get(self, request):
        """Barcha saqlangan ma'lumotlarni formatlangan holda qaytaradi"""
        with SAVED_DATA_LOCK:
            formatted_data = [{
                "timestamp": item["timestamp"],
                "image_url": item["image_url"],
                "matches_found": bool(item["student_matches"] or item["phone_matches"]),
                "match_counts": {
                    "students": sum(len(v) for v in item["student_matches"].values()),
                    "phones": sum(len(v) for v in item["phone_matches"].values())
                }
            } for item in SAVED_DATA]
            
            return Response({"count": len(SAVED_DATA), "results": formatted_data})

    def post(self, request):
        """Yangi ma'lumotlarni qabul qilishni takomillashtirilgan versiyasi"""
        try:
            data = request.data
            image_url = data.get('image_url')
            user_coords = data.get('coordinates', [])
            
            # Ma'lumotlarni validatsiya qilish
            if not image_url or not isinstance(user_coords, list):
                raise ValueError("image_url va coordinates majburiy")

            valid_coords = [c for c in user_coords if validate_coordinate(c)]
            if not valid_coords:
                raise ValueError("Yaroqli koordinatalar yo'q")

            # Koordinatalarni yuklash
            student_coords, phone_coords = load_coordinates()
            
            # Mosliklarni topish
            student_matches = match_coordinates(valid_coords, student_coords, self.MAX_THRESHOLD)
            phone_matches = match_coordinates(valid_coords, phone_coords, self.MAX_THRESHOLD)

            # Ma'lumotlarni saqlash
            entry = {
                "timestamp": datetime.now().isoformat(),
                "image_url": image_url,
                "user_coords": valid_coords,
                "student_matches": student_matches,
                "phone_matches": phone_matches
            }

            with SAVED_DATA_LOCK:
                SAVED_DATA.append(entry)
                # Xotirani boshqarish uchun eski ma'lumotlarni tozalash
                if len(SAVED_DATA) > 1000:
                    SAVED_DATA.pop(0)

            return Response({
                "status": "success",
                "matches": {
                    "student_count": sum(len(v) for v in student_matches.values()),
                    "phone_count": sum(len(v) for v in phone_matches.values())
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Xatolik: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request):
        """Ma'lumotlarni tozalash uchun optimallashtirilgan metod"""
        with SAVED_DATA_LOCK:
            SAVED_DATA.clear()
        logger.info("Barcha ma'lumotlar tozalandi")
        return Response({"status": "success"}, status=status.HTTP_204_NO_CONTENT)