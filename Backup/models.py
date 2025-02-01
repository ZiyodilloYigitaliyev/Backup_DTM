from django.db import models

# Create your models here.

class Backup(models.Model):
    list_id = models.IntegerField(unique=True, null=False, blank=True)
    category = models.CharField(max_length=255, null=False, blank=True)
    subject = models.CharField(max_length=255, null=False, blank=True)
    text = models.TextField(max_length=300, null=False, blank=True)
    options = models.TextField(max_length=300, null=False, blank=True)
    true_answer = models.CharField(max_length=55, null=False, blank=True)
    order = models.IntegerField(unique=True, null=False, blank=True)