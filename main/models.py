from django.db import models
from django.utils.timezone import now
from Backup.models import Mapping_Data

class Result_Data(models.Model):
    list_id = models.IntegerField(null=True, blank=True)
    image_url = models.URLField(max_length=200)
    phone = models.BigIntegerField(null=True, blank=True)  # phone maydoni qo'shildi

    def __str__(self):
        return f"Result for List: {self.list_id}"

class Data(models.Model):
    user_id = models.ForeignKey(Result_Data, on_delete=models.CASCADE)
    order = models.IntegerField()  
    value = models.CharField(max_length=2, null=True)
    category = models.CharField(max_length=200, null=True, blank=True)
    status = models.BooleanField(default=False)

    def __str__(self):
        return f"Data: Order {self.order} - Value {self.value} - Status {self.status}"
