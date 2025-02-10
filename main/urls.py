from django.urls import path
from .views import ResultDataCreateAPIView

urlpatterns = [
   path("upload/",  ResultDataCreateAPIView.as_view(), name="upload"),
]