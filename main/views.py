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
    """JSON fayldan koordinatalarni yuklash (list shaklida qabul qilish uchun)."""
    global COORDINATES_CACHE, COORDINATES_LAST_MODIFIED

    if not os.path.exists(COORDINATES_PATH):
        logger.error("JSON fayl topilmadi.")
        return []

    current_mtime = os.path.getmtime(COORDINATES_PATH)
    
    with COORDINATES_CACHE_LOCK:
        if COORDINATES_CACHE is not None and current_mtime == COORDINATES_LAST_MODIFIED:
            return COORDINATES_CACHE

        try:
            with open(COORDINATES_PATH, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                # JSON noto‘g‘ri formatlangan bo‘lsa, uni tuzatish
                if not isinstance(data, list) or "coordinates" not in data:
                    logger.error("JSON format noto‘g‘ri yoki 'coordinates' kaliti mavjud emas!")
                    return []
                
                coordinates = data["coordinates"]
                
                if not isinstance(coordinates, list):
                    logger.error("Koordinatalar 'list' shaklida emas!")
                    return []
                
                COORDINATES_CACHE = coordinates
                COORDINATES_LAST_MODIFIED = current_mtime
                return COORDINATES_CACHE

        except json.JSONDecodeError:
            logger.error("JSON faylni o'qishda xatolik yuz berdi.")
            return []
        except Exception as e:
            logger.error(f"Xatolik yuz berdi: {e}")
            return []

def find_matching_coordinates(user_coordinates, saved_coordinates, max_threshold=5):
    """Foydalanuvchi koordinatalarini ±5 oralig‘ida iteratsiya qilib taqqoslaydi."""
    matching = []
    
    for saved_coord in saved_coordinates:
        if not isinstance(saved_coord, list) or "x" not in saved_coord or "y" not in saved_coord:
            continue
        
        sx, sy = saved_coord["x"], saved_coord["y"]
        
        for user_coord in user_coordinates:
            if not isinstance(user_coord, list) or "x" not in user_coord or "y" not in user_coord:
                continue
            
            ux, uy = user_coord["x"], user_coord["y"]
            
            for offset in range(0, max_threshold + 1):
                if (sx + offset == ux and sy + offset == uy) or (sx - offset == ux and sy - offset == uy):
                    matching.append(saved_coord)
                    logger.info(f"Matching found: {saved_coord}")
                    break  
    
    return matching

class ProcessImageView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        with SAVED_DATA_LOCK:
            return Response({"saved_data": SAVED_DATA}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        try:
            image_url = request.data.get('image_url')
            user_coords = request.data.get('coordinates', {})
            
            if not image_url or not isinstance(user_coords, list):
                return Response(
                    {"error": "image_url va coordinates (list formatida) majburiy"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            valid_user_coords = [
                coord for coord in user_coords if isinstance(coord, list) and "x" in coord and "y" in coord
            ]
            
            saved_coords = load_coordinates()
            
            matches = find_matching_coordinates(valid_user_coords, saved_coords)
            
            data = {
                "image_url": image_url,
                "user_coordinates": user_coords,
                "matching_coordinates": matches
            }
            
            if matches:
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
