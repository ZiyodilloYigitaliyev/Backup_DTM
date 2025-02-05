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
PHONE_COORDINATES_PATH = os.path.join(BASE_DIR, 'app/coordinates/coordinates.json')

COORDINATES_CACHE = None
COORDINATES_LAST_MODIFIED = None
COORDINATES_CACHE_LOCK = Lock()
PHONE_COORDINATES_CACHE = None
PHONE_COORDINATES_LAST_MODIFIE = None
PHONE_COORDINATES_CACHE_LOCK = Lock()

def load_coordinates():
    """JSON fayllardan koordinatalarni yuklash (student_id va phone_number uchun)."""
    global COORDINATES_CACHE, COORDINATES_LAST_MODIFIED
    

    # Student ID koordinatalari yuklash
    if not os.path.exists(COORDINATES_PATH):
        logger.error("Student ID uchun JSON fayl topilmadi.")
        student_coordinates = []
    else:
        student_mtime = os.path.getmtime(COORDINATES_PATH)

        with COORDINATES_CACHE_LOCK:
            if COORDINATES_CACHE is not None and student_mtime == COORDINATES_LAST_MODIFIED:
                student_coordinates = COORDINATES_CACHE
            else:
                try:
                    with open(COORDINATES_PATH, 'r', encoding='utf-8') as file:
                        data = json.load(file)

                        if not isinstance(data, dict) or "coordinates" not in data:
                            logger.error("Student ID JSON formati noto‘g‘ri yoki 'coordinates' mavjud emas!")
                            student_coordinates = []
                        else:
                            student_coordinates = data["coordinates"]

                        COORDINATES_CACHE = student_coordinates
                        COORDINATES_LAST_MODIFIED = student_mtime

                except json.JSONDecodeError:
                    logger.error("Student ID JSON faylni o'qishda xatolik yuz berdi.")
                    student_coordinates = []
                except Exception as e:
                    logger.error(f"Student ID yuklashda xatolik: {e}")
                    student_coordinates = []
                    return student_coordinates

def load_phone_coordinates():
    global PHONE_COORDINATES_CACHE, PHONE_COORDINATES_LAST_MODIFIED

    # Phone Number koordinatalari yuklash
    if not os.path.exists(PHONE_COORDINATES_PATH):
        logger.error("Telefon raqami uchun JSON fayl topilmadi.")
        phone_coordinates = []
    else:
        phone_mtime = os.path.getmtime(PHONE_COORDINATES_PATH)

        with COORDINATES_CACHE_LOCK:
            if PHONE_COORDINATES_CACHE is not None and phone_mtime == PHONE_COORDINATES_LAST_MODIFIED:
                phone_coordinates = PHONE_COORDINATES_CACHE
            else:
                try:
                    with open(PHONE_COORDINATES_PATH, 'r', encoding='utf-8') as file:
                        data = json.load(file)

                        if not isinstance(data, dict) or "coordinates" not in data:
                            logger.error("Telefon JSON formati noto‘g‘ri yoki 'coordinates' mavjud emas!")
                            phone_coordinates = []
                        else:
                            phone_coordinates = data["coordinates"]

                        PHONE_COORDINATES_CACHE = phone_coordinates
                        PHONE_COORDINATES_LAST_MODIFIED = phone_mtime

                except json.JSONDecodeError:
                    logger.error("Telefon raqami JSON faylni o'qishda xatolik yuz berdi.")
                    phone_coordinates = []
                except Exception as e:
                    logger.error(f"Telefon raqami yuklashda xatolik: {e}")
                    phone_coordinates = []

    return phone_coordinates

        

def find_matching_coordinates(user_coordinates, student_coords, phone_coords, max_threshold=5):
    """Foydalanuvchi koordinatalarini ±5 oralig‘ida iteratsiya qilib taqqoslaydi va indeks bilan qaytaradi."""
    matching = {}  # Student ID uchun mos kelganlar
    phone_matching = {}  # Phone Number uchun mos kelganlar

    # Student koordinatalarni tekshirish
    for key, saved_list in student_coords[0].items():  # "n1", "n2", ...
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

    # **Phone Number koordinatalarni tekshirish**
    for key, saved_list in phone_coords[0].items():  # "p1", "p2", ...
        seen_phone_coords = set()  

        for index, indexed_coord in enumerate(saved_list):  
            for _, saved_coord in indexed_coord.items():  
                sx, sy = saved_coord["x"], saved_coord["y"]

                for user_coord in user_coordinates:
                    ux, uy = user_coord["x"], user_coord["y"]

                    if (sx - max_threshold <= ux <= sx + max_threshold) and (sy - max_threshold <= uy <= sy + max_threshold):
                        coord_tuple = (sx, sy)

                        if coord_tuple not in seen_phone_coords:
                            seen_phone_coords.add(coord_tuple)

                            if key not in phone_matching:
                                phone_matching[key] = []
                            phone_matching[key].append({str(index): saved_coord})

    return matching, phone_matching  # Endi ikkita alohida natija qaytariladi






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

            # Student ID va Phone Number koordinatalarini yuklash
            student_coords = load_coordinates()
            phone_coords = load_phone_coordinates()

            # O‘xshash koordinatalarni topish
            matching_coordinates, phone_number_matches = find_matching_coordinates(valid_user_coords, student_coords, phone_coords)

            data = {
                "image_url": image_url,
                "user_coordinates": user_coords,
                "matching_coordinates": matching_coordinates,  # Student ID uchun mos kelganlar
                "phone_number_matches": phone_number_matches  # Phone Number uchun mos kelganlar
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

