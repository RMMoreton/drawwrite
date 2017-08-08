"""The URL mappings for DrawWrite."""

from django.conf.urls import url

from . import views

app_name = "drawwrite" #pylint: disable=invalid-name
urlpatterns = [ #pylint: disable=invalid-name
    url(r'^$', views.index, name='index'),
    url(r'^join$', views.join_game, name='joinGame'),
    url(r'^create$', views.create_game, name='createGame'),
    url(r'^play/(?P<player_id>[0-9]+)$', views.play, name='play'),
    url(r'^ajax/checkGameStart/(?P<player_id>[0-9]+)$',
        views.check_game_start, name='checkGameStart'),
    url(r'^startGame/(?P<player_id>[0-9]+)$', views.start_game,
        name='startGame'),
    url(r'^createLink/(?P<player_id>[0-9]+)$', views.create_link,
        name='createLink'),
    url(r'^checkRoundDone/(?P<player_id>[0-9]+)$', views.check_round_done,
        name='checkRoundDone'),
    url(r'^checkGameDone/(?P<game_id>[0-9]+)$', views.check_game_done,
        name='checkGameDone'),
    url(r'^showGame/(?P<game_id>[0-9]+)$', views.show_game,
        name='showGame'),
    url(r'^showChain/(?P<player_id>[0-9]+)$', views.show_chain,
        name='showChain'),
]
