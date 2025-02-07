from django.db import models

# Create your models here.

class Mapping_Data(models.Model):
    list_id = models.IntegerField(null=True, blank=True)
    category = models.CharField(max_length=200, null=True, blank=True)
    true_answer = models.JSONField(default=list)
    order = models.JSONField(default=list)
