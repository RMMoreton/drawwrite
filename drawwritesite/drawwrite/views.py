# Imports {{{
import logging

from . import services

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import IntegrityError
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from drawwrite.models import Chain, Game, DrawLink, Player, WriteLink
from drawwrite.forms import IndexForm

from os import path

from uuid import uuid4

from base64 import b64decode

from itertools import zip_longest
# }}}

LOG = logging.getLogger(__name__)

# Index {{{
def index(request):
    """
    The landing page of the app.
    """
    LOG.debug('enter index view')

    # Create the form that we'll put on this page.
    form = IndexForm()

    LOG.debug('exit index view')
    return render(request, 'drawwrite/index.html', {
        # Add the form.
        'form': form,
        # Add any error data.
        'errorTitle': request.session.pop('errorTitle', None),
        'errorDescription': request.session.pop('errorDescription', None),
    })
# }}}

# joinGame {{{
def joinGame(request):
    """
    Proccess data that a user sends when they want to join a game.
    """
    LOG.debug('entering join game view')

    # Send all non-POSTs to the index.
    if request.method != 'POST':
        LOG.debug('attempted non-supported method {0}'.format(request.method))
        return redirect('drawwrite:index')

    # Get the form from the POSTed data.
    form = IndexForm(request.POST)

    # Invalid forms redirect to the index with an error.
    if not form.is_valid():
        LOG.debug('username {0} or gamename {1} invalid'.format(
            form.data['username'], form.data['gamename']))
        request.session['errorTitle'] = 'Invalid input'
        request.session['errorDescription'] = ' '.join((
            'Your Name and the Game Name must only contain letters, numbers,',
            'underscores, and hyphens.'
        ))
        return redirect('drawwrite:index')

    # Valid forms are processed.
    gamename = form.cleaned_data['gamename']
    username = form.cleaned_data['username']

    # Get the game. On error, add error objects to the session and redirect
    # to index.
    game = None
    try:
        game = Game.objects.get(name=gamename)
    except Game.DoesNotExist as e:
        LOG.debug('tried to join non-existant game {0}'.format(gamename))
        request.session['errorTitle'] = 'Non-existent game'
        request.session['errorDescription'] = ' '.join((
            'The game that you attempted to join, {0},'.format(gamename),
            'does not exist. Please check that you entered it correctly.',
        ))
        return redirect('drawwrite:index')

    # Add a player to the game. On error, add error objects to the session and
    # redirect to index.
    player = None
    try:
        player = services.newPlayer(game, username, False)
    except services.GameAlreadyStarted as e:
        LOG.debug('could not add {0} to game {1}'.format(
            username, game.name
        ))
        request.session['errorTitle'] = 'Game started'
        request.session['errorDescription'] = ' '.join((
            'The game that you attempted to join has already started. Please',
            'either join a different game or start your own game.',
        ))
        return redirect('drawwrite:index')
    # TODO: Don't assume that all IntegrityError's mean that the game name is
    #   already taken. There are plenty of other explanations that I'm
    #   silencing by doing this.
    except IntegrityError as e:
        LOG.exception('player with {0} already exists in game {1}'.format(
            username, gamename
        ))
        request.session['errorTitle'] = 'Player exists'
        request.session['errorDescription'] = ' '.join((
            'The player name that you entered is already in use in the game',
            'that you are trying to join. Please choose a new player name',
            'and try again.'
        ))
        return redirect('drawwrite:index')

    # Redirect to that game's page.
    LOG.debug('exiting join game view')
    return redirect('drawwrite:play', player.pk)
# }}}

# createGame {{{
def createGame(request):
    """
    Create a game according to the values the user specified in the form.
    """
    LOG.debug('entering create game view')

    # Send all non-POSTs to the index.
    if request.method != 'POST':
        LOG.debug('attempted non-supported method {0}'.format(request.method))
        return redirect('drawwrite:index')

    # Get the form from the POSTed data.
    form = IndexForm(request.POST)

    # Invalid forms redirect to the index with an error.
    if not form.is_valid():
        LOG.debug('username {0} or gamename {1} invalid'.format(
            form.data['username'], form.data['gamename']))
        request.session['errorTitle'] = 'Invalid input'
        request.session['errorDescription'] = ' '.join((
            'Your Name and the Game Name must only contain letters, numbers,',
            'underscores, and hyphens.'
        ))
        return redirect('drawwrite:index')

    # Valid forms are processed.
    gamename = form.cleaned_data['gamename']
    username = form.cleaned_data['username']
    
    # Create game. On error, add error objects to the session and redirect
    # to index.
    game = None
    try:
        game = services.newGame(gamename)
    # TODO: Don't assume that all IntegrityError's mean that the game name is
    #   already taken. There are plenty of other explanations that I'm
    #   silencing by doing this.
    except services.GameCurrentlyBeingMade as e:
        LOG.info('game name {0} is being made'.format(gamename))
        request.session['errorTitle'] = 'Game being created'
        request.session['errorDescription'] = 'Game {0} is already being created'.format(gamename)
        return redirect('drawwrite:index')
    except IntegrityError as e:
        LOG.info('Exception creating game: ' + e.getMessage)
        request.session['errorTitle'] = 'Unknown error'
        request.session['errorDescription'] = e.getMessage()
        return redirect('drawwrite:index')

    # Create a player for that game. On error, add error objects to the
    # session and redirect to index.
    player = None
    try:
        player = services.newPlayer(game, username, True)
    # TODO: Don't assume that all IntegrityError's mean that the user name is
    #   already taken. There are plenty of other explanations that I'm
    #   silencing by doing this.
    except IntegrityError as e:
        LOG.debug('a new game has an invalid player {0}'.format(username))
        request.session['errorTitle'] = 'Player name taken'
        request.session['errorDescription'] = ' '.join((
            'The player name that you entered, {0},'.format(username),
            ' is already taken for the game that you entered. Please',
            'try a different one.',
        ))
        return redirect('drawwrite:index')

    # Redirect to that game's page.
    LOG.debug('exiting create game view')
    return redirect('drawwrite:play', player.pk)
# }}}

# play {{{
def play(request, playerId):
    """
    The page on which players play the game.
    """
    LOG.debug('enter play view')

    # Get their player from the database using the id in the path. On error,
    # set error session attributes and redirect to index.
    player = None
    try:
        player = Player.objects.get(pk=playerId)
    except Player.DoesNotExist as e:
        LOG.error('non-existant player attempt: {0}'.format(playerId))
        request.session['errorTitle'] = 'Player Does Not Exist'
        request.session['errorDescription'] = ' '.join((
            'You attempted to access a non-existant player. Plase do not',
            'do that.'
        ))
        return redirect('drawwrite:index')
    LOG.debug('successfully retreived player {0}'.format(playerId))

    # Get the game from the player object.
    game = player.game
    LOG.debug('successfully retreived game for player {0}'.format(playerId))

    # If the game hasn't started, show the player the waiting screen.
    if not game.started:
        LOG.debug('game for player {0} has not started'.format(playerId))

        # Get a list of all players in this game.
        allPlayers = Player.objects.filter(game=game)
        LOG.debug('got players in game with player {0}'.format(playerId))

        # Get the creator of the game.
        creator = None
        for p in allPlayers:
            if p.wasCreator:
                creator = p
        LOG.debug('creator of game is {0}'.format(creator.name))

        # Render the waiting screen with all of those players.
        LOG.debug('showing player {0} the waiting screen'.format(playerId))
        return render(request, 'drawwrite/waiting.html', {
            'allPlayers' : allPlayers,
            'playerId' : playerId,
            'created' : player.wasCreator,
            'creator' : creator,
        })
    LOG.debug('game for player {0} has started'.format(playerId))

    # The game has started. Check if it's also finished.
    if game.roundNum >= game.numPlayers:
        LOG.debug('game finished, redirect to view page')
        return redirect('drawwrite:showGame', game.pk)

    # The game has started, so decide whether to show the waiting page.
    if player.currentRound == game.roundNum + 1:

        # If the player's round equals the number of players in the game,
        # show the 'wait for game completion' game.
        if player.currentRound == player.game.numPlayers:
            LOG.debug('show game finished waiting page')
            return render(request, 'drawwrite/gameWaiting.html', {
                'gameId' : game.pk,
            })

        # If the game isn't finished, show the waiting page for the next round.
        LOG.debug('show waiting page, this user is done with current round')
        return render(request, 'drawwrite/roundWaiting.html', {
            'playerId' : playerId,
        })

    # If the player's round doesn't equal the game's round, something is fishy.
    elif not player.currentRound == game.roundNum:
        LOG.error(' '.join((
            'player {0} has round {1},'.format(playerId, player.currentRound),
            'while game {0} has round {1},'.format(game.pk, game.roundNum),
            'which should not be possible'
        )))
        # TODO come up with a better thing to show the user in this case
        return HttpResponseBadRequest()

    # Figure out which position's chain this player
    # should have access to next.
    chainPosToGet = (player.position + game.roundNum) % game.numPlayers
    LOG.debug('player {0} needs position {1}s chain'.format(playerId, chainPosToGet))

    # Get the owner of the chain that player will edit.
    chainOwner = None
    try:
        chainOwner = Player.objects.filter(
            game=game
        ).get(
            position=chainPosToGet
        )
    except Player.DoesNotExist:
        LOG.error('player with game {0} and pos {1} does not exist'.format(game.pk, chainPosToGet))
        request.session['errorTitle'] = 'Player Does Not Exist'
        request.session['errorDescription'] = ' '.join((
            'You tried to get a player that does not exist. Sorry for',
            'the inconvenience.',
        ))
        return redirect('drawwrite:index')
    LOG.debug('got chainOwner ({0}) for player {1}'.format(chainOwner.pk, playerId))

    # Get the chain for the player.
    chain = None
    try:
        chain = Chain.objects.get(player=chainOwner)
    except Chain.DoesNotExist:
        # Make a chain for this player.
        chain = services.newChain(player)
    LOG.debug('got chain for user {0}'.format(playerId))

    # If the chain has no links, show the player a screen to enter their first
    # text link.
    if chain.nextLinkPosition == 0:
        LOG.debug('returning page for first link for user {0}'.format(playerId))
        return render(request, 'drawwrite/chainAdd.html', {
            'prevLink': False,
            'prevLinkType': '',
            'prevLink': None,
            'playerId': playerId,
        })

    # Figure out what type of link the player needs to make.
    prevLinkPos = chain.nextLinkPosition - 1
    prevLink = None
    prevLinkType = ''
    if prevLinkPos % 2 == 0:
        prevLinkType = 'write'
        prevLink = WriteLink.objects.get(chain=chain,
                linkPosition=prevLinkPos)
    else:
        prevLinkType = 'draw'
        prevLink = DrawLink.objects.get(chain=chain,
                linkPosition=prevLinkPos)

    # Show the player a page to add the next link type.
    LOG.debug('exit add to chain view')
    return render(request, 'drawwrite/chainAdd.html', {
        'prevLinkType': prevLinkType,
        'prevLink': prevLink,
        'playerId': playerId,
    })
# }}}

# checkGameStart {{{
def checkGameStart(request, playerId):
    LOG.debug('checking game status for player {0}'.format(playerId))

    # Get the player.
    player = None
    try:
        player = Player.objects.get(pk=playerId)
    except Player.DoesNotExist:
        LOG.error('non-existant player: {0}'.format(playerId))
        return HttpResponseBadRequest()
    LOG.debug('successfully found player {0}'.format(playerId))

    # If the player's game has not started, return an updated list of names.
    if not player.game.started:
        LOG.debug('player {0} game has not started'.format(playerId))

        # Get all the players in the game.
        allPlayers = Player.objects.filter(game=player.game)
        LOG.debug('got all players in game with {0}'.format(playerId))

        # Create a list of all player names.
        names = []
        for player in allPlayers:
            names.append(player.name)
        LOG.debug('made list of all player names')

        # Return the data we need.
        return JsonResponse({'started': False, 'names': names})

    # If the player's game has started, return an object indicating as much.
    return JsonResponse({'started': True, 'names': []})
# }}}

# startGame {{{
def startGame(request, playerId):
    LOG.debug('starting game of player {0}'.format(playerId))

    # Make sure method is POST.
    if not request.method == 'POST':
        LOG.error('attempted to GET to start game')
        return HttpResponseBadRequest()

    # Get the player.
    player = None
    try:
        player = Player.objects.get(pk=playerId)
    except Player.DoesNotExist:
        LOG.error('non-existant player {0}'.format(playerId))
        return HttpResponseBadRequest()
    LOG.debug('successfully got player {0}'.format(playerId))

    # Set the player's game to 'started'.
    services.startGame(player.game)
    LOG.debug('set players game to started')

    # Redirect to 'play'.
    LOG.debug('redirecting to play')
    return redirect('drawwrite:play', playerId)
# }}}

# createLink {{{
def createLink(request, playerId):
    """
    Accept POST data and create a new link in the chain that playerId should
    be adding to.
    """
    LOG.debug('creating link for player {0}'.format(playerId))

    # Only accept POSTs
    if not request.method == 'POST':
        LOG.error('should have POSTed data')
        return HttpResponseNotAllowed(['POST'])
    LOG.debug('got POST data for player {0}'.format(playerId))

    # Get the player.
    player = None
    try:
        player = Player.objects.get(pk=playerId)
    except Player.DoesNotExist:
        LOG.error('non-existant player {0}'.format(playerId))
        request.session['errorTitle'] = 'Player Does Not Exist'
        request.session['errorDescription'] = ' '.join((
            'The player that you tried to create a link for does not exist.',
            'We apologize for the inconvenience.',
        ))
        return redirect('drawwrite:index')
    LOG.debug('got the player with pk {0}'.format(playerId))

    # Calculate the position of the player that this playerId is adding to.
    chainOwnerPosition = (player.position + player.game.roundNum) % player.game.numPlayers
    LOG.debug('player {0} needs chain of player {1}'.format(playerId, chainOwnerPosition))

    # Get the owner of the chain this player is adding to.
    try:
        chainOwner = Player.objects.filter(
            game=player.game
        ).get(
            position=chainOwnerPosition
        )
    except Player.DoesNotExist:
        LOG.error('player with game {0} and position {1} does not exist'.format(player.game.pk, chainOwnerPosition))
        request.session['errorTitle'] = 'Player Does Not Exist'
        request.session['description'] = ' '.join((
            'You attempted to access a player that does not exist. We are',
            'sorry for the inconvenience.'
        ))
        return redirect('drawwrite:index')
    LOG.debug('successfully got chain owner for player {0}'.format(playerId))

    # Get the player's chain.
    chain = None
    try:
        chain = Chain.objects.get(player=chainOwner)
    except Chain.DoesNotExist:
        LOG.error('player {0} should have a chain but does not'.format(playerId))
        request.session['errorTitle'] = 'Player Has No Chain'
        request.session['errorDescription'] = ' '.join((
            'The player that you tried to create a link for does not have',
            'a chain, but that should not be possible. We apologize for',
            'the inconvenience.',
        ))
        return redirect('drawwrite:index')
    LOG.debug('got the chain for player with pk {0}'.format(playerId))

    # Figure out what type of link to make.
    if chain.nextLinkPosition % 2 == 0:
        # The POST data needs to have the 'description' field or something
        # is wrong.
        if 'description' not in request.POST.keys():
            LOG.error(' '.join((
                'should be making write link, but did not receive any',
                'writing in the POSTed data',
            )))
            return HttpResponseBadRequest()
        LOG.debug('making new write link for player {0}'.format(playerId))

        # Make the new write link.
        services.newWriteLink(chain, request.POST.get('description'), player)

    else:
        # The POST data needs to have the 'drawing' field or something
        # is wrong.
        if 'drawing' not in request.POST.keys():
            LOG.error(' '.join((
                'should be making a draw link, but did not receive any',
                'drawing data in the POSTed data',
            )))
            return HttpResponseBadRequest()
        LOG.debug('got image data to save')

        # Make sure the data starts with 'data:image/png;base64,'
        dataString = request.POST.get('drawing')
        if not dataString.startswith('data:image/png;base64,'):
            LOG.error('got bad image data: started with {0}'.format(dataString[0:15]))
            return HttpResponseBadRequest()
        LOG.debug('got good(ish) image data')

        # Shave off the stuff from above.
        dataString = dataString.split(';base64,')[1]
        LOG.debug('split off the ;base64, stuff')

        # Decode the base64 data.
        binaryData = b64decode(dataString)
        LOG.debug('decoded base64 data')

        # Make a file-like object out of the data.
        fileName = "link-{0}-{1}.png".format(playerId, chain.nextLinkPosition)
        fileObj = ContentFile(binaryData, name=fileName)
        LOG.debug('made file with name {0}')

        # Make the draw link.
        services.newDrawLink(chain, fileObj, player)
        LOG.debug('created draw link, file has name {0}')

    # Increase the 'numPlayersFinishedCurrentRound' of this game.
    services.playerFinished(player)

    # Redirect to 'play'.
    return redirect('drawwrite:play', playerId)
# }}}

# checkRoundDone {{{
def checkRoundDone(request, playerId):
    """
    Check if the round of the current game is completed. Return a javascript
    object that has a list of every player's name that has not completed the round.
    """
    LOG.debug('checking if round is completed for player {0}'.format(playerId))

    # Get the player.
    player = None
    try:
        player = Player.objects.get(pk=playerId)
    except Player.DoesNotExist:
        LOG.error('attempted to get player that does not exist')
        request.session['errorTitle'] = 'Player Does Not Exist'
        request.session['errorDescription'] = ' '.join((
            'The player that you attempted to get does not exist. We are',
            'sorry for the inconvenience.',
        ))
        return redirect('drawwrite:index')
    LOG.debug('successfully got player {0}'.format(playerId))

    # Check if the game round equals the player's round. If so, then the
    # player is allowed to move on. Otherwise, they're not.
    if player.game.roundNum == player.currentRound:
        LOG.debug('round is completed')

        # Return an object saying that the round is done.
        return JsonResponse({'finished': True})
    LOG.debug('round is not completed')

    # Get all players in the game who have not completed the
    # current round.
    try:
        playersStillPlaying = Player.objects.filter(game=player.game).filter(currentRound__lt=player.currentRound)
    except BaseException as e:
        LOG.error(e)
        raise
    LOG.debug('got list of players still playing')

    # Turn the players into a list of names.
    namesStillPlaying = []
    for p in playersStillPlaying:
        namesStillPlaying.append(p.name)
    LOG.debug('got list of names of players still playing')

    # Return an object saying that the round is not done.
    return JsonResponse({
        'finished': False,
        'stillPlaying': namesStillPlaying,
    })
# }}}

# checkGameDone {{{
def checkGameDone(request, gameId):
    LOG.debug('checking if game {0} is done'.format(gameId))

    # Get the game.
    game = None
    try:
        game = Game.objects.get(pk=gameId)
    except Game.DoesNotExist:
        LOG.error('tried to get non-existant game {0}'.format(gameId))
        # TODO better error stuff
        return HttpResponseBadRequest
    LOG.debug('got game {0}'.format(gameId))

    # Check if the round equals the number of players.
    if game.roundNum == game.numPlayers:
        return JsonResponse({'finished': True})

    # Get a list of players whose current round equals the game's round.
    try:
        playersStillPlaying = Player.objects.filter(game=game).filter(currentRound=game.roundNum)
    except BaseException as e:
        LOG.error(e)
        raise
    LOG.debug('got list of players still playing')

    # Turn that list of players into a list of names.
    names = []
    for p in playersStillPlaying:
        names.append(p.name)
    LOG.debug('created list of names of players still playing')

    return JsonResponse({
        'finished': False,
        'stillPlaying': names,
    })
# }}}

# showGame {{{
def showGame(request, gameId):
    LOG.debug('showing game {0}'.format(gameId))

    # Get the game.
    game = None
    try:
        game = Game.objects.get(pk=gameId)
    except Game.DoesNotExist:
        LOG.error('tried to get non-existant game {0}'.format(gameId))
        # TODO better error here
        return HttpResponseBadRequest()
    LOG.debug('got game {0}'.format(gameId))

    # Get all players associated with that game.
    players = Player.objects.filter(game=game)

    # Render the game view page.
    return render(request, 'drawwrite/game.html', {
        'players': players,
        'gameName': game.name,
    })
# }}}

# showChain {{{
def showChain(request, playerId):
    LOG.debug('showing chain of player {0}'.format(playerId))

    # Get the player.
    player = None
    try:
        player = Player.objects.get(pk=playerId)
    except Player.DoesNotExist:
        LOG.error('tried to get non-existant player {0}'.format(playerId))
        # TODO better error messege
        return HttpResponseBadRequest()
    LOG.debug('got player {0}'.format(playerId))

    # Get the chain.
    chain = None
    try:
        chain = Chain.objects.get(player=player)
    except Chain.DoesNotExist:
        LOG.error('tried to get non-existant chain for player {0}'.format(playerId))
        # TODO better error message
        return HttpResponseBadRequest()
    LOG.debug('got chain for player {0}'.format(playerId))

    # Get all the write links and all the draw links.
    writeLinks = WriteLink.objects.filter(chain=chain)
    drawLinks = DrawLink.objects.filter(chain=chain)

    # Make a list of all the links in the chain.
    links = []
    for write, draw in zip_longest(writeLinks, drawLinks):
        if write is not None:
            links.append(write)
        if draw is not None:
            links.append(draw)
    LOG.debug('made list of all links for player {0}'.format(playerId))


    # Render the chain view.
    return render(request, 'drawwrite/chain.html', {
        'links': links,
        'player': player,
    })
# }}}
