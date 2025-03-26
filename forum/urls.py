from django.urls import path
from . import views


app_name = 'forum'

urlpatterns = [
    path('', views.thread_list, name='thread_list'),
    path('thread/<int:thread_id>/', views.thread_detail, name='thread_detail'),
    path('thread/new/', views.new_thread, name='new_thread'),
    path('thread/<int:thread_id>/delete/', views.delete_thread, name='delete_thread'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
]