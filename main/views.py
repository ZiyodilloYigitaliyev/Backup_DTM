import os
import csv
import uuid
import logging
from io import StringIO
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .models import ProcessedTest, ProcessedTestResult

logger = logging.getLogger(__name__)

def is_within_tolerance(coord1, coord2, tolerance=5):
    return abs(coord1[0] - coord2[0]) <= tolerance and abs(coord1[1] - coord2[1]) <= tolerance

def extract_data_from_bubbles(bubbles, reference_coords):
    for key, coord_list in reference_coords.items():
        if any(is_within_tolerance(coord, bubble) for bubble in bubbles for coord in coord_list):
            return key
    return None

class ProcessImageView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        transaction_id = str(uuid.uuid4())[:8]
        try:
            csv_file = request.FILES.get('file')
            img_url = request.data.get('img_url', '').strip()
            
            if not csv_file:
                return Response({"error": "CSV fayl taqdim etilishi shart"}, status=status.HTTP_400_BAD_REQUEST)

            csv_data = csv_file.read().decode('utf-8')
            csv_io = StringIO(csv_data)
            reader = csv.DictReader(csv_io)

            bubbles = []
            student_id_coords = {}
            phone_number_coords = {}
            answers = {}

            for row in reader:
                x, y = int(row.get('x_coord', 0)), int(row.get('y_coord', 0))
                data_type = row.get('data_type', '').strip().lower()
                value = row.get('value', '').strip()

                if data_type == 'bubble':
                    bubbles.append((x, y))
                elif data_type == 'student_id' and value:
                    student_id_coords.setdefault(value, []).append((x, y))
                elif data_type == 'phone_number' and value:
                    phone_number_coords.setdefault(value, []).append((x, y))
                elif data_type == 'answer':
                    question = row.get('question', '').strip()
                    if question:
                        answers[question] = value

            student_id = extract_data_from_bubbles(bubbles, student_id_coords)
            phone_number = extract_data_from_bubbles(bubbles, phone_number_coords)

            if not student_id:
                return Response({"error": "Student ID aniqlanmadi"}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                processed_test = ProcessedTest.objects.create(
                    student_id=student_id,
                    phone_number=phone_number,
                    img_url=img_url,
                    bubbles=bubbles
                )
                
                for question, answer in answers.items():
                    ProcessedTestResult.objects.create(
                        student=processed_test,
                        student_answer={question: answer},
                        is_correct=True, 
                        score=1
                    )
            
            return Response({
                "message": "Ma'lumotlar saqlandi",
                "transaction_id": transaction_id,
                "details": {
                    "student_id": student_id,
                    "phone_number": phone_number,
                    "answers_count": len(answers)
                }
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Xatolik yuz berdi: {e}")
            return Response({"error": "Ichki server xatosi"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
