from django.db import models

# Create your models here.

class Backup(models.Model):
    list_id = models.IntegerField(unique=True, null=False, blank=True)
    true_answer = models.CharField(max_length=55, null=False, blank=True)
    order = models.IntegerField(unique=True, null=False, blank=True)
