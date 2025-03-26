from django.urls import path
from . import views

app_name = 'auctions'

urlpatterns = [
    path('', views.auction_list, name='auction_list'),
    path('auction/<int:auction_id>/', views.auction_detail, name='auction_detail'),
    path('auction/new/', views.create_auction, name='create_auction'),
]