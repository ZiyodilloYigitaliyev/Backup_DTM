from django.db import models

# Create your models here.

class ProcessedID(models.Model):
    list_id = models.IntegerField(null=True, default=0, blank=True)

class Mapping_Data(models.Model):
    true_answersID = models.ForeignKey(ProcessedID, null=True, blank=True, on_delete=models.CASCADE)
    category = models.CharField(max_length=200, null=True, blank=True)
    true_answer = models.CharField(max_length=20, null=True, blank=True)
    order = models.IntegerField(null=True, blank=True)
