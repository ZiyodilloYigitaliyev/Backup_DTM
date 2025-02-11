from django.urls import path
from .views import ResultDataCreateAPIView, PDFResultRetrieveAPIView

urlpatterns = [
   path("upload/",  ResultDataCreateAPIView.as_view(), name="upload"),
   path("get-pdf/",  PDFResultRetrieveAPIView.as_view(), name="get-pdf"),
]