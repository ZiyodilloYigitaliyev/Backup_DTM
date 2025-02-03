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
    logger.info("Koordinatalarni ajratish boshlandi. Bubbles soni: %d", len(bubbles))
    if not bubbles or not coordinates_dict:
        return None

    for key, coord_list in coordinates_dict.items():
        for coord in coord_list:
            if coord in bubbles:
                return {key: coord}
    return None

def load_coordinates_from_csv(csv_path):
    data = {}
    try:
        with open(csv_path, 'r') as file:
            reader = csv.reader(file)
            next(reader) 
            for row in reader:
                if not row:
                    continue
                key = row[0]
                try:
                    coordinates = [(int(row[i]), int(row[i+1])) for i in range(1, len(row), 2)]
                except (ValueError, IndexError):
                    continue
                data[key] = coordinates
        return data
    except FileNotFoundError:
        raise
    except Exception as e:
        raise

def load_student_id_coordinates_from_csv(csv_path):
    data = {}
    try:
        with open(csv_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                student_id = row.get('value', '').strip()
                if not student_id:
                    continue
                try:
                    x = int(row.get('x_coord'))
                    y = int(row.get('y_coord'))
                except (ValueError, TypeError):
                    continue
                coord = (x, y)
                if student_id in data:
                    data[student_id].append(coord)
                else:
                    data[student_id] = [coord]
        return data
    except FileNotFoundError:
        raise
    except Exception as e:
        raise

def is_within_tolerance(coord1, coord2, tolerance=5):
    x1, y1 = coord1
    x2, y2 = coord2
    return abs(x1 - x2) <= tolerance and abs(y1 - y2) <= tolerance

def extract_student_id(bubbles, student_coords, tolerance=5):
    if not bubbles or not student_coords:
        return None
    for student_id, coord_list in student_coords.items():
        for coord_csv in coord_list:
            for coord_bubble in bubbles:
                if is_within_tolerance(coord_csv, coord_bubble, tolerance):
                    return student_id
    return None

class ProcessImageView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        transaction_id = str(uuid.uuid4())[:8]
        try:
            csv_file = request.FILES.get('file')
            file_url = request.data.get('file_url')
            if not csv_file:
                return Response({"error": "CSV fayl yuborilmagan"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                csv_data = csv_file.read().decode('utf-8')
            except Exception:
                return Response({"error": "CSV faylni o'qishda xato"}, status=status.HTTP_400_BAD_REQUEST)
            csv_io = StringIO(csv_data)
            reader = csv.DictReader(csv_io)

            bubbles = []
            phone_number = None
            marked_answers = {}

            for row in reader:
                data_type = row.get('data_type', '').strip().lower()
                if data_type == 'bubble':
                    try:
                        x = int(row.get('x_coord'))
                        y = int(row.get('y_coord'))
                        bubbles.append((x, y))
                    except Exception:
                        continue
                elif data_type == 'phone_number':
                    phone_number = row.get('value', '').strip()
                elif data_type == 'answer':
                    question = row.get('question', '').strip()
                    answer = row.get('value', '').strip()
                    if question:
                        marked_answers[question] = answer

            student_coords = load_student_id_coordinates_from_csv(ID_PATH)
            extracted_student_id = extract_student_id(bubbles, student_coords, tolerance=5)

            if not extracted_student_id:
                return Response({"error": "Student ID aniqlanmadi"}, status=status.HTTP_400_BAD_REQUEST)

            question_coords = load_coordinates_from_csv(COORDINATES_PATH)
            extracted_answers = extract_from_coordinates(bubbles, question_coords)

            with transaction.atomic():
                processed_test = ProcessedTest.objects.create(
                    phone_number=phone_number,
                    bubbles=bubbles
                )
                if marked_answers:
                    for q, a in marked_answers.items():
                        ProcessedTestResult.objects.create(
                            student=processed_test,
                            student_answer=json.dumps({q: a}),
                            is_correct=True,
                            score=1
                        )
            return Response({
                "message": "Ma'lumotlar saqlandi",
                "transaction_id": transaction_id,
                "details": {
                    "extracted_student_id": extracted_student_id,
                    "phone_number": phone_number,
                    "answers_count": len(marked_answers)
                }
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": "Ichki server xatosi"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
