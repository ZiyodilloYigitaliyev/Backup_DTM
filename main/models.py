from django.db import models
from django.utils.timezone import now

class ImageData(models.Model):
    image_url = models.URLField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Yaratilgan vaqt


class Coordinate(models.Model):
    image = models.ForeignKey(ImageData, on_delete=models.CASCADE, related_name="coordinates")
    x = models.IntegerField()
    y = models.IntegerField()



class result(models.Model):
    file = models.URLField()
    phone = models.IntegerField()
    student_id = models.CharField(max_length=10)
    total_score = models.FloatField()

    def __str__(self):
        return f"{self.student_id} - {self.total_score}"
    
