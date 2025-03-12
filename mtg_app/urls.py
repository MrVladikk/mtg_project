from django.urls import path
from . import views

app_name = 'mtg_app'

urlpatterns =[
    path('', views.home, name='home'),
    path('cards/', views.card_list, name='card_list'),
    path('cards/<int:card_id>/', views.card_detail, name='card_detail'),
    path('sets/', views.set_list, name='set_list'),
    path('sets/<int:set_id>/', views.set_detail, name='set_detail'),
    path('decks/', views.deck_list, name='deck_list'),
    path('decks/<int:deck_id>/', views.deck_detail, name='deck_detail'),
]