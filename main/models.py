from django.db import models
from Backup.models import Backup

class ProcessedTest(models.Model):
    file = models.FileField(upload_to='uploads/')
    file_url = models.URLField(max_length=500, default=False)
    bubbles = models.JSONField(null=False, default=False)
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
# === Model ===
class ProcessedData(models.Model):    
    x_coord = models.IntegerField()
    y_coord = models.IntegerField()
    data_type = models.CharField(max_length=50)

    def __str__(self):
        return f"({self.x_coord}, {self.y_coord}) - {self.data_type}"