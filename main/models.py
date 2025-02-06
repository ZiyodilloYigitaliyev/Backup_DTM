from django.db import models
from Backup.models import Mapping_Data

class allCategory(models.Model):
    category = models.CharField(max_length=200)
# ==Models==
class ProcessedData(models.Model):
    CATEGORY_CHOICES = [
        ('matching', 'Matching Coordinates'),
        ('user_id', 'User ID Coordinates'),
        ('phone', 'Phone Coordinates'),
        ('answer', 'Answer Coordinates'),
    ]

    x_coord = models.FloatField()
    y_coord = models.FloatField() 
    data_type = models.CharField(max_length=255)
    category = models.CharField(max_length=200, choices=CATEGORY_CHOICES) 

class ProcessedTest(models.Model):
    file = models.FileField(upload_to='uploads/')
    file_url = models.URLField(max_length=500, default=False)
    phone_number = models.CharField(max_length=20, unique=True, default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    student_id = models.BigAutoField(primary_key=True)
    total_score = models.FloatField(default=0)
    
    def __str__(self):
        return f"ScannedImage {self.id}: {self.file_url}"
    
class ProcessedTestResult(models.Model):
    student = models.ForeignKey(ProcessedTest, related_name='results', on_delete=models.CASCADE)
    student_answer = models.CharField(max_length=10)
    is_correct = models.BooleanField(default=False)
    processed_at = models.DateTimeField(auto_now_add=True)
    score = models.FloatField(default=0)
 
