from django.urls import path
from .views import (
    health,
    chat,
    create_session,
    list_sessions,
    get_session,
    delete_session,
    list_messages,
)

urlpatterns = [
    path('health/', health, name='Health'),
    path('chat/', chat, name='chat'),
    path('sessions/', list_sessions, name='list_sessions'),
    path('sessions/create/', create_session, name='create_session'),
    path('sessions/<uuid:session_id>/', get_session, name='get_session'),
    path('sessions/<uuid:session_id>/delete/', delete_session, name='delete_session'),
    path('sessions/<uuid:session_id>/messages/', list_messages, name='list_messages'),
]
