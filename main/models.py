from django.db import models
from django.utils.timezone import now

class ProcessedData(models.Model):
    list_id = models.IntegerField()
    category = models.CharField(max_length=200)
    order = models.IntegerField()
    answer = models.CharField(max_length=255)
    status = models.BooleanField() # True if answer is correct, False otherwise
    
