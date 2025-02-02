from django.db import models

# Create your models here.

class Backup(models.Model):
    list_id = models.IntegerField(null=False, blank=True)
    true_answer = models.JSONField(default=list)
    order = models.JSONField(default=list)
