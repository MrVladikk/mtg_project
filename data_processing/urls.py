from django.urls import path
from . import views

app_name = 'data_processing' # Пространство имен для URL (хорошая практика)

urlpatterns = [
    path('upload-csv/', views.upload_csv_view, name='upload_csv'),
]