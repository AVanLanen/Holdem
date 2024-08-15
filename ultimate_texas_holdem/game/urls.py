# game/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.game_view, name='game_view'),
    path('start/', views.start_game, name='start_game'),
    path('join/<int:game_id>/', views.join_game, name='join_game'),
    path('game/<int:game_id>/', views.game_action, name='game_action'),
    path('game/<int:game_id>/place_bets/', views.place_initial_bets, name='place_initial_bets'),
    path('game/<int:game_id>/start_new_round/', views.start_new_round, name='start_new_round'),
    path('delete-game/<int:game_id>/', views.delete_game, name='delete_game'),
    path('game/<int:game_id>/results/', views.game_results, name='game_results'),
]