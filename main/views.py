import logging
import os
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from conf.settings import BASE_DIR
from threading import Lock  # For thread safety

logger = logging.getLogger(__name__)

SAVED_DATA = []
SAVED_DATA_LOCK = Lock()  # Thread-safe access to SAVED_DATA
COORDINATES_PATH = os.path.join(BASE_DIR, 'app/coordinates/coordinates.json')

# Coordinates caching mechanism
COORDINATES_CACHE = None
COORDINATES_LAST_MODIFIED = None
COORDINATES_CACHE_LOCK = Lock()  # Thread-safe cache updates

def load_coordinates():
    """JSON fayldan koordinatalarni yuklash (optimallashtirilgan versiya)."""
    global COORDINATES_CACHE, COORDINATES_LAST_MODIFIED

    if not os.path.exists(COORDINATES_PATH):
        return []

    current_mtime = os.path.getmtime(COORDINATES_PATH)
    
    with COORDINATES_CACHE_LOCK:
        if (COORDINATES_CACHE is not None and 
            current_mtime == COORDINATES_LAST_MODIFIED):
            return COORDINATES_CACHE

        try:
            with open(COORDINATES_PATH, 'r', encoding='utf-8') as file:
                data = json.load(file)
                coordinates = data.get("coordinates", [])
                
                if not isinstance(coordinates, list):
                    logger.error("Koordinatalar list shaklida emas!")
                    COORDINATES_CACHE = []
                else:
                    # Validate and filter coordinates once
                    COORDINATES_CACHE = [
                        coord for coord in coordinates
                        if isinstance(coord, dict) 
                        and "x" in coord 
                        and "y" in coord
                    ]
                
                COORDINATES_LAST_MODIFIED = current_mtime
                return COORDINATES_CACHE
                
        except json.JSONDecodeError:
            logger.error("JSON faylni o'qishda xatolik yuz berdi.")
            return []
        except Exception as e:
            logger.error(f"Xatolik yuz berdi: {e}")
            return []

def find_matching_coordinates(user_coordinates, saved_coordinates, max_threshold=5):
    """O'xshash koordinatalarni tezkor qidirish."""
    matching = []
    # Precompute user coordinate ranges
    user_ranges = [
        (
            uc["x"] - max_threshold,
            uc["x"] + max_threshold,
            uc["y"] - max_threshold,
            uc["y"] + max_threshold
        )
        for uc in user_coordinates
    ]
    
    for saved_coord in saved_coordinates:
        sx, sy = saved_coord["x"], saved_coord["y"]
        # Check against all user ranges with short-circuit
        if any(
            (x_min <= sx <= x_max) and 
            (y_min <= sy <= y_max)
            for x_min, x_max, y_min, y_max in user_ranges
        ):
            matching.append(saved_coord)
            logger.info(f"Matching found: {saved_coord}")
            
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
            
            # Validate input
            if not image_url or not isinstance(user_coords, list):
                return Response(
                    {"error": "image_url va coordinates (list formatida) majburiy"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Filter valid user coordinates
            valid_user_coords = []
            invalid_user_coords = []
            
            for coord in user_coords:
                if isinstance(coord, dict) and "x" in coord and "y" in coord:
                    valid_user_coords.append(coord)
                else:
                    invalid_user_coords.append(coord)
            
            # Log invalid coordinates
            if invalid_user_coords:
                logger.warning(
                    f"{len(invalid_user_coords)} ta noto‘g‘ri formatdagi koordinatalar"
                )
            
            # Load cached coordinates
            saved_coords = load_coordinates()
            
            # Find matches with optimized function
            matches = find_matching_coordinates(valid_user_coords, saved_coords)
            
            data = {
                "image_url": image_url,
                "user_coordinates": user_coords,
                "matching_coordinates": matches
            }
            
            # Thread-safe data update
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