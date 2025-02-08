from django.urls import path
from .views import upload_image, ResultRetrieveView

urlpatterns = [
   path("upload/", upload_image, name="upload_image"),
   path("result/", ResultRetrieveView.as_view(), name="result-retrieve"),
]