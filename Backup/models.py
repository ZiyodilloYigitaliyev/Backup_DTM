from django.db import models

class Mapping_Data(models.Model):
    list_id = models.IntegerField(null=True, blank=True)
    school = models.CharField(max_length=255, null=True, blank=True)
    category = models.CharField(max_length=200, null=True, blank=True)
    true_answer = models.CharField(max_length=255, null=True, blank=True)
    order = models.IntegerField(null=True, blank=True)
