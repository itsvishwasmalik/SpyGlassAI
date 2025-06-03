from django.urls import path
from . import views_api

urlpatterns = [
    path('hello/', views_api.sayHello),
    path('get_research_paper_details/', views_api.get_research_paper_details),
    path('chat/send/', views_api.send_message),
    path('chat/conversations/create/', views_api.create_conversation),
    path('chat/conversations/', views_api.get_conversations),
    path('chat/conversations/<str:conversation_id>/', views_api.delete_conversation),
]
