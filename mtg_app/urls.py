from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import custom_logout
from .views import delete_deck

app_name = 'mtg_app'

urlpatterns =[
    path('', views.home, name='home'),
    path('cards/', views.card_list, name='card_list'),
    path('cards/<int:card_id>/', views.card_detail, name='card_detail'),
    path('sets/', views.set_list, name='set_list'),
    path('sets/<int:set_id>/', views.set_detail, name='set_detail'),
    path('decks/', views.deck_list, name='deck_list'),
    path('decks/<int:deck_id>/', views.deck_detail, name='deck_detail'),
    path('register/', views.register, name='register'),
    path('add_card/', views.add_card, name='add_card'),
    path('add_deck/', views.add_deck, name='add_deck'),
    path('logout/', custom_logout, name='logout'),
    path('deck/delete/<int:deck_id>/', delete_deck, name='delete_deck'),
    ]