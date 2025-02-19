from django.urls import path
from .views import ResultDataCreateAPIView, PDFResultRetrieveAPIView, ResultDataByDateRetrieveAPIView

urlpatterns = [
   path("upload/",  ResultDataCreateAPIView.as_view(), name="upload"),
   path("get-pdf/",  PDFResultRetrieveAPIView.as_view(), name="get-pdf"),
   path("get-result/", ResultDataByDateRetrieveAPIView.as_view(), name="get-result_by_date")
]