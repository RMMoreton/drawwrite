from django.conf.urls import url

from . import views

app_name="drawwrite"
urlpatterns=[
        url(r'^$', views.index, name='index'),
        url(r'^join$', views.joinGame, name='joinGame'),
        url(r'^create$', views.createGame, name='createGame'),
        url(r'^play/(?P<playerId>[0-9]+)$', views.play, name='play'),
        url(r'^ajax/checkGameStart/(?P<playerId>[0-9]+)$',
            views.checkGameStart, name='checkGameStart'),
        url(r'^startGame/(?P<playerId>[0-9]+)$', views.startGame,
            name='startGame'),
        url(r'^createLink/(?P<playerId>[0-9]+)$', views.createLink,
            name='createLink'),
        url(r'^checkRoundDone/(?P<playerId>[0-9]+)$', views.checkRoundDone,
            name='checkRoundDone'),
        url(r'^checkGameDone/(?P<gameId>[0-9]+)$', views.checkGameDone,
            name='checkGameDone'),
        url(r'^showGame/(?P<gameId>[0-9]+)$', views.showGame,
            name='showGame'),
        url(r'^showChain/(?P<playerId>[0-9]+)$', views.showChain,
            name='showChain'),
        ]
