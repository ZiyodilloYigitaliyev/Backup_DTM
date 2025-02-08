from django.db import models
from django.utils.timezone import now

class ImageData(models.Model):
    image_url = models.URLField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Yaratilgan vaqt

    def save(self, *args, **kwargs):
        ImageData.objects.all().delete()  # Eski ma’lumotlarni o‘chiramiz
        super().save(*args, **kwargs)

    def __str__(self):
        return self.image_url

class Coordinate(models.Model):
    image = models.ForeignKey(ImageData, on_delete=models.CASCADE, related_name="coordinates")
    x = models.IntegerField()
    y = models.IntegerField()


# from Backup.models import Mapping_Data

# # ==Models==
# class ProcessedData(models.Model):
#     CATEGORY_CHOICES = [
#         ('matching', 'Matching Coordinates'),
#         ('user_id', 'User ID Coordinates'),
#         ('phone', 'Phone Coordinates'),
#         ('answer', 'Answer Coordinates'),
#     ]
#     x_coord = models.FloatField()
#     y_coord = models.FloatField()
#     data_type = models.CharField(max_length=255)
#     answer = models.CharField(max_length=255, null=True, blank=True)
#     category = models.CharField(max_length=200, choices=CATEGORY_CHOICES)  

# class ProcessedTest(models.Model):
#     file_url = models.URLField(null=True, max_length=500, default=False)
#     image_url = models.URLField(max_length=500, default=False)
#     phone_number = models.CharField(max_length=20, unique=True, default=False)
#     uploaded_at = models.DateTimeField(auto_now_add=True)
#     student_id = models.CharField(null=True, max_length=10, default=False)
#     total_score = models.FloatField(default=0)
    
#     def __str__(self):
#         return self.student_id
    
# class ProcessedTestResult(models.Model):
#     student = models.ForeignKey(ProcessedTest, related_name='results', on_delete=models.CASCADE)
#     student_answer = models.CharField(max_length=10)
#     order = models.IntegerField(null=True, blank=True)
#     is_correct = models.BooleanField(default=False)
#     processed_at = models.DateTimeField(auto_now_add=True)
#     score = models.FloatField(default=0)
    
#     def __str__(self):
#         return self.student_answer
 
