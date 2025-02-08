from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
import logging
# from .models import ProcessedData, ProcessedTest, ProcessedTestResult, Mapping_Data
from rest_framework.decorators import api_view
from .models import ImageData
from .serializers import ImageDataSerializer, ResultSerializer

@api_view(["POST"])
def upload_image(request): 
    serializer = ImageDataSerializer(data=request.data)
    
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Image data saved successfully"}, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResultRetrieveView(APIView):
    """
    GET so'rovi orqali query param 'student_id' keladi.
    Agar bazada shu student_id bo'yicha natija topilsa, file URL, id va telefon raqamini JSON formatda yuboradi.
    """
    def get(self, request, format=None):
        student_id = request.query_params.get("student_id")
        if not student_id:
            return Response({"error": "Query parameter 'student_id' talab qilinadi."},
                            status=status.HTTP_400_BAD_REQUEST)
        
        try:
            obj = result.objects.get(student_id=student_id)
        except result.DoesNotExist:
            return Response({"error": "Berilgan student_id bo'yicha natija topilmadi."},
                            status=status.HTTP_404_NOT_FOUND)
        
        serializer = ResultSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
