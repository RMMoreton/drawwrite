"""All the views for DrawWrite."""

# Imports {{{
import logging

from base64 import b64decode

from itertools import zip_longest

from django.core.files.base import ContentFile
from django.db import IntegrityError
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import redirect, render

from drawwrite.forms import CreateGameForm, JoinGameForm
from drawwrite.models import Chain, Game, DrawLink, Player, WriteLink

from . import services
from .bracefmt import BraceFormatter as __
# }}}

LOG = logging.getLogger(__name__)

# index {{{
def index(request):
    """
    The front page of the app.
    """
    LOG.debug("enter index")

    # Create the two forms that we'll put on this page.
    create_form = CreateGameForm()
    join_form = JoinGameForm()

    # TODO errors shouldn't get added by title and description, but by number.
    #      Then I should look up the title and description from that number.
    return render(request, 'drawwrite/index.html', {
        'create_form': create_form,
        'join_form': join_form,
        'error_title': request.session.pop('error_title', None),
        'error_description': request.session.pop('error_description', None),
    })
# }}}

# join_game {{{
def join_game(request):
    """
    Proccess data that a user sends when they want to join a game.
    """
    LOG.debug('enter')

    # Send all non-POSTs to the index.
    if request.method != 'POST':
        LOG.info(__('attempted non-supported method {0}', request.method))
        request.session['error_title'] = 'Unsupported method'
        request.session['error_description'] = (
            'You\'re not allowed to send {0} requests to that endpoint.'.format(request.method),
        )
        return redirect('drawwrite:index')

    # Get the form from the POSTed data.
    form = JoinGameForm(request.POST)

    # Invalid forms redirect to the index with an error.
    if not form.is_valid():
        LOG.debug(__(
            'name {0} or gamename {1} invalid',
            form.data['username'],
            form.data['gamename'],
        ))
        request.session['error_title'] = 'Invalid input'
        request.session['error_description'] = ' '.join((
            'Your Name and the Game Name must only contain letters, numbers,',
            'underscores, and hyphens.',
        ))
        return redirect('drawwrite:index')

    # Valid forms are processed.
    gamename = form.cleaned_data['gamename']
    username = form.cleaned_data['username']

    # Get the game. On error, add error objects to the session and redirect
    # to index.
    # TODO extract this, possibly to services.py
    games = Game.objects.filter( #pylint: disable=no-member
        name=gamename,
    ).filter(
        started=False,
    )
    if len(games) > 1:
        LOG.error(__('somehow, two games with name {0} are being created', gamename))
        request.session['error_title'] = 'Non-unique game name'
        request.session['error_description'] = 'Could not find a unique game for you to join'
        return redirect('drawwrite:index')
    if len(games) < 1:
        LOG.error(__('tried to join non-existant game {0}', gamename))
        request.session['error_title'] = 'Non-existent game'
        request.session['error_description'] = ' '.join((
            'The game that you attempted to join, {0},'.format(gamename),
            'does not exist. Please check that you entered it correctly.',
        ))
        return redirect('drawwrite:index')
    game = games[0]
    LOG.debug(__('got game for player {0}', username))

    # Add a player to the game. On error, add error objects to the session and
    # redirect to index.
    player = None
    try:
        player = services.new_player(game, username, False)
    except services.GameAlreadyStarted:
        LOG.debug(__('could not add {0} to game {1}', username, game.name))
        request.session['error_title'] = 'Game started'
        request.session['error_description'] = ' '.join((
            'The game that you attempted to join has already started. Please',
            'either join a different game or start your own game.',
        ))
        return redirect('drawwrite:index')
    # TODO don't assume that all IntegrityError's mean that the game name is
    #   already taken. There are plenty of other explanations that I'm
    #   silencing by doing this.
    except IntegrityError:
        LOG.exception(__(
            'player with {0} already exists in game {1}',
            username,
            gamename,
        ))
        request.session['error_title'] = 'Player exists'
        request.session['error_description'] = ' '.join((
            'The player name that you entered is already in use in the game',
            'that you are trying to join. Please choose a new player name',
            'and try again.',
        ))
        return redirect('drawwrite:index')

    # Redirect to that game's page.
    LOG.debug('exiting join game view')
    return redirect('drawwrite:play', player.pk)
# }}}

# create_game {{{
def create_game(request):
    """
    Create a game according to the values the user specified in the form.
    """
    LOG.debug('entering create game view')

    # Send all non-POSTs to the index.
    if request.method != 'POST':
        LOG.debug(__('attempted non-supported method {0}', request.method))
        return redirect('drawwrite:index')

    # Get the form from the POSTed data.
    form = CreateGameForm(request.POST)

    # Invalid forms redirect to the index with an error.
    if not form.is_valid():
        #LOG.debug(__(
        #    'username {0} or gamename {1} invalid',
        #    form.data['username'],
        #    form.data['gamename'],
        #))
        LOG.debug(__(
            'form error: {0}',
            form.errors,
        ))
        request.session['error_title'] = 'Invalid input'
        request.session['error_description'] = ' '.join((
            'Your Name and the Game Name must only contain letters, numbers,',
            'underscores, and hyphens.',
        ))
        return redirect('drawwrite:index')

    # Valid forms are processed.
    gamename = form.cleaned_data['gamename']
    username = form.cleaned_data['username']

    # Create game. On error, add error objects to the session and redirect
    # to index.
    # TODO handle other errors that could happen?
    game = services.new_game(gamename)
    if game is None:
        request.session['error_title'] = 'Game being created'
        request.session['error_description'] = (
            'The game you are trying to join, {0}, is already being created'
        ).format(gamename)

    # Create a player for that game. On error, add error objects to the
    # session and redirect to index.
    player = None
    try:
        player = services.new_player(game, username, True)
    # TODO don't assume that all IntegrityError's mean that the user name is
    #   already taken. There are plenty of other explanations that I'm
    #   silencing by doing this.
    except services.NameTaken as exception:
        LOG.error('player name already taken')
        request.session['error_title'] = 'Player name taken'
        request.session['error_description'] = exception.message()
        return redirect('drawwrite:index')
    except IntegrityError:
        LOG.error(__('a new game has an invalid player {0}', username))
        request.session['error_title'] = 'Player name taken'
        request.session['error_description'] = ' '.join((
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
def play(request, player_id):
    """
    The page on which players play the game.
    """
    LOG.debug('enter play view')

    # Get their player from the database using the id in the path. On error,
    # set error session attributes and redirect to index.
    player = None
    try:
        player = Player.objects.get(pk=player_id) #pylint: disable=no-member
    except Player.DoesNotExist: #pylint: disable=no-member
        LOG.error(__('non-existant player attempt: {0}', player_id))
        request.session['error_title'] = 'Player Does Not Exist'
        request.session['error_description'] = ' '.join((
            'You attempted to access a non-existant player. Plase do not',
            'do that.',
        ))
        return redirect('drawwrite:index')
    LOG.debug(__('successfully retreived player {0}', player_id))

    # Get the game from the player object.
    game = player.game
    LOG.debug(__('successfully retreived game for player {0}', player_id))

    # If the game hasn't started, show the player the waiting screen.
    if not game.started:
        LOG.debug(__('game for player {0} has not started', player_id))

        # Get a list of all players in this game.
        all_players = Player.objects.filter(game=game) #pylint: disable=no-member
        LOG.debug(__('got players in game with player {0}', player_id))

        # Get the creator of the game.
        creator = None
        for player in all_players:
            if player.was_creator:
                creator = player
        LOG.debug(__('creator of game is {0}', creator.name))

        # Render the waiting screen with all of those players.
        LOG.debug(__('showing player {0} the waiting screen', player_id))
        return render(request, 'drawwrite/waiting.html', {
            'all_players' : all_players,
            'player_id' : player_id,
            'created' : player.was_creator,
            'creator' : creator,
        })
    LOG.debug(__('game for player {0} has started', player_id))

    # The game has started. Check if it's also finished.
    if game.round_num >= game.num_players:
        LOG.debug('game finished, redirect to view page')
        return redirect('drawwrite:showGame', game.pk)

    # The game has started, so decide whether to show the waiting page.
    if player.current_round == game.round_num + 1:

        # If the player's round equals the number of players in the game,
        # show the 'wait for game completion' game.
        if player.current_round == player.game.num_players:
            LOG.debug('show game finished waiting page')
            return render(request, 'drawwrite/gameWaiting.html', {
                'game_id' : game.pk,
            })

        # If the game isn't finished, show the waiting page for the next round.
        LOG.debug('show waiting page, this user is done with current round')
        return render(request, 'drawwrite/roundWaiting.html', {
            'player_id' : player_id,
        })

    # If the player's round doesn't equal the game's round, something is fishy.
    elif not player.current_round == game.round_num:
        LOG.error(__(
            'player {0} has round {1}, while game {2} has round {3}',
            player_id,
            player.current_round,
            game.pk,
            game.round_num,
        ))
        # TODO come up with a better thing to show the user in this case
        return HttpResponseBadRequest()

    # Figure out which position's chain this player should have access to next.
    chain_pos_to_get = (player.position + game.round_num) % game.num_players
    LOG.debug(__('player {0} needs position {1}s chain', player_id, chain_pos_to_get))

    # Get the owner of the chain that player will edit.
    chain_owner = None
    try:
        chain_owner = Player.objects.filter( #pylint: disable=no-member
            game=game,
        ).get(
            position=chain_pos_to_get,
        )
    except Player.DoesNotExist: #pylint: disable=no-member
        LOG.error(__(
            'player with game {0} and pos {1} does not exist',
            game.pk,
            chain_pos_to_get,
        ))
        request.session['error_title'] = 'Player Does Not Exist'
        request.session['error_description'] = ' '.join((
            'You tried to get a player that does not exist. Sorry for',
            'the inconvenience.',
        ))
        return redirect('drawwrite:index')
    LOG.debug(__('got chain_owner ({0}) for player {1}', chain_owner.pk, player_id))

    # Get the chain for the player.
    chain = None
    try:
        chain = Chain.objects.get(player=chain_owner) #pylint: disable=no-member
    except Chain.DoesNotExist: #pylint: disable=no-member
        # Make a chain for this player.
        chain = services.new_chain(player)
    LOG.debug(__('got chain for user {0}', player_id))

    # If the chain has no links, show the player a screen to enter their first
    # text link.
    if chain.next_link_position == 0:
        LOG.debug(__('returning page for first link for user {0}', player_id))
        return render(request, 'drawwrite/chainAdd.html', {
            'prev_link_type': '',
            'prev_link': None,
            'player_id': player_id,
        })

    # Figure out what type of link the player needs to make.
    prev_link_pos = chain.next_link_position - 1
    prev_link = None
    prev_link_type = ''
    if prev_link_pos % 2 == 0:
        prev_link_type = 'write'
        prev_link = WriteLink.objects.get( #pylint: disable=no-member
            chain=chain,
            link_position=prev_link_pos
        )
    else:
        prev_link_type = 'draw'
        prev_link = DrawLink.objects.get( #pylint: disable=no-member
            chain=chain,
            link_position=prev_link_pos
        )

    # Show the player a page to add the next link type.
    LOG.debug('exit add to chain view')
    return render(request, 'drawwrite/chainAdd.html', {
        'prev_link_type': prev_link_type,
        'prev_link': prev_link,
        'player_id': player_id,
    })
# }}}

# check_game_start {{{
def check_game_start(request, player_id): #pylint: disable=unused-argument
    """Check if the passed player's game has started."""

    LOG.debug(__('checking game status for player {0}', player_id))

    # Get the player.
    player = None
    try:
        player = Player.objects.get(pk=player_id) #pylint: disable=no-member
    except Player.DoesNotExist: #pylint: disable=no-member
        LOG.error(__('non-existant player: {0}', player_id))
        return HttpResponseBadRequest()
    LOG.debug(__('successfully found player {0}', player_id))

    # If the player's game has not started, return an updated list of names.
    if not player.game.started:
        LOG.debug(__('player {0} game has not started', player_id))

        # Get all the players in the game.
        all_players = Player.objects.filter(game=player.game) #pylint: disable=no-member
        LOG.debug(__('got all players in game with {0}', player_id))

        # Create a list of all player names.
        names = []
        for player in all_players:
            names.append(player.name)
        LOG.debug('made list of all player names')

        # Return the data we need.
        return JsonResponse({'started': False, 'names': names})

    # If the player's game has started, return an object indicating as much.
    return JsonResponse({'started': True, 'names': []})
# }}}

# start_game {{{
def start_game(request, player_id):
    """Start the game of the player identified by player_id"""

    LOG.debug(__('starting game of player {0}', player_id))

    # Make sure method is POST.
    if not request.method == 'POST':
        LOG.error('attempted to GET to start game')
        return HttpResponseBadRequest()

    # Get the player.
    player = None
    try:
        player = Player.objects.get(pk=player_id) #pylint: disable=no-member
    except Player.DoesNotExist: #pylint: disable=no-member
        LOG.error(__('non-existant player {0}', player_id))
        return HttpResponseBadRequest()
    LOG.debug(__('successfully got player {0}', player_id))

    # Set the player's game to 'started'.
    services.start_game(player.game)
    LOG.debug('set players game to started')

    # Redirect to 'play'.
    LOG.debug('redirecting to play')
    return redirect('drawwrite:play', player_id)
# }}}

# create_link {{{
def create_link(request, player_id):
    """
    Accept POST data and create a new link in the chain that player_id should
    be adding to.
    """
    LOG.debug(__('creating link for player {0}', player_id))

    # Only accept POSTs
    if not request.method == 'POST':
        LOG.error('should have POSTed data')
        return HttpResponseNotAllowed(['POST'])
    LOG.debug(__('got POST data for player {0}', player_id))

    # Get the player.
    player = None
    try:
        player = Player.objects.get(pk=player_id) #pylint: disable=no-member
    except Player.DoesNotExist: #pylint: disable=no-member
        LOG.error(__('non-existant player {0}', player_id))
        request.session['error_title'] = 'Player Does Not Exist'
        request.session['error_description'] = ' '.join((
            'The player that you tried to create a link for does not exist.',
            'We apologize for the inconvenience.',
        ))
        return redirect('drawwrite:index')
    LOG.debug(__('got the player with pk {0}', player_id))

    # Calculate the position of the player that this player_id is adding to.
    chain_owner_pos = (player.position + player.game.round_num) % player.game.num_players
    LOG.debug(__('player {0} needs chain of player {1}', player_id, chain_owner_pos))

    # Get the owner of the chain this player is adding to.
    try:
        chain_owner = Player.objects.filter( #pylint: disable=no-member
            game=player.game,
        ).get(
            position=chain_owner_pos,
        )
    except Player.DoesNotExist: #pylint: disable=no-member
        LOG.error(__(
            'player with game {0} and position {1} does not exist',
            player.game.pk,
            chain_owner_pos,
        ))
        request.session['error_title'] = 'Player Does Not Exist'
        request.session['description'] = ' '.join((
            'You attempted to access a player that does not exist. We are',
            'sorry for the inconvenience.',
        ))
        return redirect('drawwrite:index')
    LOG.debug(__('successfully got chain owner for player {0}', player_id))

    # Get the player's chain.
    chain = None
    try:
        chain = Chain.objects.get(player=chain_owner) #pylint: disable=no-member
    except Chain.DoesNotExist: #pylint: disable=no-member
        LOG.error(__('player {0} should have a chain but does not', player_id))
        request.session['error_title'] = 'Player Has No Chain'
        request.session['error_description'] = ' '.join((
            'The player that you tried to create a link for does not have',
            'a chain, but that should not be possible. We apologize for',
            'the inconvenience.',
        ))
        return redirect('drawwrite:index')
    LOG.debug(__('got the chain for player with pk {0}', player_id))

    # Figure out what type of link to make.
    if chain.next_link_position % 2 == 0:
        # The POST data needs to have the 'description' field or something
        # is wrong.
        if 'description' not in request.POST.keys():
            LOG.error(' '.join((
                'should be making write link, but did not receive any',
                'writing in the POSTed data',
            )))
            return HttpResponseBadRequest()
        LOG.debug(__('making new write link for player {0}', player_id))

        # Make the new write link.
        services.new_write_link(chain, request.POST.get('description'), player)

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
        data_string = request.POST.get('drawing')
        if not data_string.startswith('data:image/png;base64,'):
            LOG.error(__('got bad image data: started with {0}', data_string[0:15]))
            return HttpResponseBadRequest()
        LOG.debug('got good(ish) image data')

        # Shave off the stuff from above.
        data_string = data_string.split(';base64,')[1]
        LOG.debug('split off the ;base64, stuff')

        # Decode the base64 data.
        binary_data = b64decode(data_string)
        LOG.debug('decoded base64 data')

        # Make a file-like object out of the data.
        file_name = "link-{0}-{1}.png".format(player_id, chain.next_link_position)
        file_obj = ContentFile(binary_data, name=file_name)
        LOG.debug(__('made file with name {0}', file_name))

        # Make the draw link.
        services.new_draw_link(chain, file_obj, player)
        LOG.debug(__('created draw link, file has name {0}', file_name))

    # Increase the 'num_players_finished_current_round' of this game.
    services.player_finished(player)

    # Redirect to 'play'.
    return redirect('drawwrite:play', player_id)
# }}}

# check_round_done {{{
def check_round_done(request, player_id):
    """
    Check if the round of the current game is completed. Return a javascript
    object that has a list of every player's name that has not completed the round.
    """
    LOG.debug(__('checking if round is completed for player {0}', player_id))

    # Get the player.
    player = None
    try:
        player = Player.objects.get(pk=player_id) #pylint: disable=no-member
    except Player.DoesNotExist: #pylint: disable=no-member
        LOG.error('attempted to get player that does not exist')
        request.session['error_title'] = 'Player Does Not Exist'
        request.session['error_description'] = ' '.join((
            'The player that you attempted to get does not exist. We are',
            'sorry for the inconvenience.',
        ))
        return redirect('drawwrite:index')
    LOG.debug(__('successfully got player {0}', player_id))

    # Check if the game round equals the player's round. If so, then the
    # player is allowed to move on. Otherwise, they're not.
    if player.game.round_num == player.current_round:
        LOG.debug('round is completed')

        # Return an object saying that the round is done.
        return JsonResponse({'finished': True})
    LOG.debug('round is not completed')

    # Get all players in the game who have not completed the
    # current round.
    try:
        players_still_playing = Player.objects.filter( #pylint: disable=no-member
            game=player.game,
        ).filter(
            current_round__lt=player.current_round,
        )
    except BaseException as exception:
        LOG.error(exception)
        raise
    LOG.debug('got list of players still playing')

    # Turn the players into a list of names.
    names_still_playing = []
    for player in players_still_playing:
        names_still_playing.append(player.name)
    LOG.debug('got list of names of players still playing')

    # Return an object saying that the round is not done.
    return JsonResponse({
        'finished': False,
        'still_playing': names_still_playing,
    })
# }}}

# check_game_done {{{
def check_game_done(request, game_id): #pylint: disable=unused-argument
    """Check if the game with the passed game_id is finished."""

    LOG.debug(__('checking if game {0} is done', game_id))

    # Get the game.
    game = None
    try:
        game = Game.objects.get(pk=game_id) #pylint: disable=no-member
    except Game.DoesNotExist: #pylint: disable=no-member
        LOG.error(__('tried to get non-existant game {0}', game_id))
        # TODO better error stuff
        return HttpResponseBadRequest
    LOG.debug(__('got game {0}', game_id))

    # Check if the round equals the number of players.
    if game.round_num == game.num_players:
        return JsonResponse({'finished': True})

    # Get a list of players whose current round equals the game's round.
    try:
        players_still_playing = Player.objects.filter( #pylint: disable=no-member
            game=game,
        ).filter(
            current_round=game.round_num,
        )
    except BaseException as exception:
        LOG.error(exception)
        raise
    LOG.debug('got list of players still playing')

    # Turn that list of players into a list of names.
    names_still_playing = []
    for player in players_still_playing:
        names_still_playing.append(player.name)
    LOG.debug('created list of names of players still playing')

    # Return an object saying that the round is not done.
    return JsonResponse({
        'finished': False,
        'still_playing': names_still_playing,
    })
# }}}

# show_game {{{
def show_game(request, game_id):
    """Show a completed game."""

    LOG.debug(__('showing game {0}', game_id))

    # Get the game.
    game = None
    try:
        game = Game.objects.get(pk=game_id) #pylint: disable=no-member
    except Game.DoesNotExist: #pylint: disable=no-member
        LOG.error(__('tried to get non-existant game {0}', game_id))
        # TODO better error here
        return HttpResponseBadRequest()
    LOG.debug(__('got game {0}', game_id))

    # Get all players associated with that game.
    players = Player.objects.filter(game=game) #pylint: disable=no-member

    # Render the game view page.
    # Change gameName to game_name
    return render(request, 'drawwrite/game.html', {
        'players': players,
        'game_name': game.name,
    })
# }}}

# show_chain {{{
def show_chain(request, player_id):
    """Show a completed chain."""

    LOG.debug(__('showing chain of player {0}', player_id))

    # Get the player.
    player = None
    try:
        player = Player.objects.get(pk=player_id) #pylint: disable=no-member
    except Player.DoesNotExist: #pylint: disable=no-member
        LOG.error(__('tried to get non-existant player {0}', player_id))
        # TODO better error messege
        return HttpResponseBadRequest()
    LOG.debug(__('got player {0}', player_id))

    # Get the chain.
    chain = None
    try:
        chain = Chain.objects.get(player=player) #pylint: disable=no-member
    except Chain.DoesNotExist: #pylint: disable=no-member
        LOG.error(__('tried to get non-existant chain for player {0}', player_id))
        # TODO better error message
        return HttpResponseBadRequest()
    LOG.debug(__('got chain for player {0}', player_id))

    # Get all the write links and all the draw links.
    write_links = WriteLink.objects.filter(chain=chain) #pylint: disable=no-member
    draw_links = DrawLink.objects.filter(chain=chain) #pylint: disable=no-member

    # Make a list of all the links in the chain.
    links = []
    for write, draw in zip_longest(write_links, draw_links):
        if write is not None:
            links.append(write)
        if draw is not None:
            links.append(draw)
    LOG.debug(__('made list of all links for player {0}', player_id))


    # Render the chain view.
    return render(request, 'drawwrite/chain.html', {
        'links': links,
        'player': player,
    })
# }}}
