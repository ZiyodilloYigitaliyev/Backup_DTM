from django.db import models
from django.utils.timezone import now
from Backup.models import Mapping_Data
import uuid

class Result_Data(models.Model):
    list_id = models.IntegerField(null=True, blank=True)
    image_url = models.URLField(max_length=200)
    phone = models.BigIntegerField(null=True, blank=True)
    school = models.CharField(max_length=255, null=True, blank=True, default="")  # yangi maydon
    question_class = models.IntegerField(null=True, blank=True, default=0)       # yangi maydon
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Result for List: {self.list_id}"

class Data(models.Model):
    user_id = models.ForeignKey(Result_Data, on_delete=models.CASCADE)
    order = models.IntegerField()  
    value = models.CharField(max_length=2, null=True)
    category = models.CharField(max_length=200, null=True, blank=True)
    subject = models.CharField(max_length=200, null=True, blank=True, default="")  # yangi maydon
    status = models.BooleanField(default=False)

    def __str__(self):
        return f"Data: Order {self.order} - Value {self.value} - Status {self.status}"

class PDFResult(models.Model):
    user_id = models.CharField("Foydalanuvchi ID", max_length=255)
    phone = models.CharField("Telefon", max_length=20)
    pdf_url = models.URLField("PDF URL", blank=True, null=True)
    created_at = models.DateTimeField("Yaratilgan vaqt", auto_now_add=True)

    def __str__(self):
        return f"PDFResult - {self.user_id}"

    class Meta:
        verbose_name = "PDF Natija"
        verbose_name_plural = "PDF Natijalar"