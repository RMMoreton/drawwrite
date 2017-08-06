"""Provide database transaction services."""

# Imports {{{
import logging

from django.db import transaction
from django.db import IntegrityError

from .models import Chain, DrawLink, Game, Player, WriteLink
from .bracefmt import BraceFormatter as __
# }}}

LOG = logging.getLogger(__name__)

# new_game {{{
@transaction.atomic
def new_game(name):
    """Return a new game with name set to the passed name."""

    LOG.debug(__('creating new game: {0}', name))
    games_with_same_name = Game.objects.filter( #pylint: disable=no-member
        name=name,
    ).filter(
        started=False,
    )
    if games_with_same_name:
        LOG.info(__('attempted to create duplicate game: {0}', name))
        return None
    try:
        ret = Game(name=name)
        ret.save()
    except Exception as exception:
        LOG.error(__('exception while creating game: {0}', exception))
        raise
    LOG.debug(__('saved new game: {0}', name))
    return ret
# }}}

# start_game {{{
@transaction.atomic
def start_game(game):
    """Set the game's 'started' attribute to True."""

    # TODO catch errors, log, and raise?
    LOG.debug(__('starting game: {0}', game.pk))
    game.started = True
    game.save()
    LOG.debug(__('saved game: {0}', game.pk))
    return
# }}}

# player_finished {{{
@transaction.atomic
def player_finished(player):
    """Record that the given player has finished the current round."""

    LOG.debug(__(
        'increasing the number of finished players for game {0}',
        player.game.pk,
    ))

    # Make sure the game has started.
    if not player.game.started:
        raise GameNotStarted(
            'The game must have started for a player to complete a round',
        )

    # Make sure the number of players who have finished isn't greater then the
    # number of players in the game.
    if player.game.num_finished_current_round >= player.game.num_players:
        raise IntegrityError('Too many players have completed the current round')

    # Make sure that the user isn't trying to finish a round that they've
    # already finished.
    if not player.current_round == player.game.round_num:
        raise IntegrityError('A players round is not in sync with the game round')

    # Add one to the player's round.
    player.current_round += 1
    player.save()

    # Add one to the number of players who have finished the current round.
    player.game.num_finished_current_round += 1
    player.game.save()

    # Check if the round is complete.
    if player.game.num_finished_current_round == player.game.num_players:
        next_round(player.game)

    LOG.debug(__('increased num_finished_current_round for game {0}', player.game.pk))
# }}}

# next_round {{{
@transaction.atomic
def next_round(game):
    """Take a game to it's next round."""

    LOG.debug(__('increasing round for game {0}', game.pk))

    # Make sure the game has started.
    if not game.started:
        raise GameNotStarted('You cannot increase the round of an unstarted game')

    # Make sure the number of players who have completed the current round
    # equals the number of players in the game.
    if not game.numPlayers == game.num_finished_current_round:
        raise WaitForPlayers('Not all players have completed the current round')

    # Increase the round, set num_players_finished_current_round to 0.
    game.round_num += 1
    game.num_finished_current_round = 0
    game.save()

    LOG.debug(__('round increased for game {0}', game.pk))
# }}}

# new_player {{{
@transaction.atomic
def new_player(game, name, was_creator):
    """
    Return a new player for the passed game and increase the game's number
    of players.
    """

    LOG.debug(__('creating new player with name {0}', name))
    if game.started:
        LOG.error(__(
            'could not add player to game {0} because that game has already started',
            name,
        ))
        raise GameAlreadyStarted(
            'It is not possible to add a player to a game that has already started',
        )
    # Get other players in this game with the same name.
    players_same_game_same_name = Player.objects.filter( #pylint: disable=no-member
        game=game,
    ).filter(
        name=name,
    )
    if players_same_game_same_name:
        LOG.error(__('player {0} already exists in game {1}', name, game.name))
        return None
    ret = Player(
        game=game,
        position=game.num_players,
        name=name,
        was_creator=was_creator,
    )
    ret.save()
    LOG.debug('saved player')
    game.num_players += 1
    game.save()
    LOG.debug('increased game num_players by 1')
    return ret
# }}}

# new_chain {{{
@transaction.atomic
def new_chain(player):
    """Create a new chain for the given user."""

    LOG.debug('creating new player')
    ret = Chain(player=player)
    ret.save()
    LOG.debug('saved new player')
    return ret
# }}}

# new_draw_link {{{
@transaction.atomic
def new_draw_link(chain, file_obj, added_by):
    """
    Return a new draw link for the passed chain, or None if the next link
    for the passed chain shouldn't be a draw link.
    """

    LOG.debug('creating new draw link')
    if chain.next_link_position % 2 == 0:
        LOG.error('attempted to create draw link at an invalid position')
        return None
    ret = DrawLink(
        drawing=file_obj,
        link_position=chain.next_link_position,
        chain=chain,
        added_by=added_by,
    )
    ret.save()
    LOG.debug('saved new draw link')
    chain.next_link_position += 1
    chain.save()
    LOG.debug('increased chain link position')
    return ret
# }}}

# new_write_link {{{
@transaction.atomic
def new_write_link(chain, text, added_by):
    """
    Return a new write link for the passed chain, or None if the next link
    for the passed chain shouldn't be a write link.
    """
    LOG.debug('creating new write link')
    if chain.next_link_position % 2 == 1:
        LOG.error('attempted to create write link in invalid position')
        return None
    ret = WriteLink(
        text=text,
        link_position=chain.next_link_position,
        chain=chain,
        added_by=added_by,
    )
    ret.save()
    LOG.debug('saved new write link')
    chain.next_link_position += 1
    chain.save()
    LOG.debug('increased chain link position')
    return ret
# }}}

# GameAlreadyStarted {{{
class GameAlreadyStarted(IntegrityError): #pylint: disable=too-few-public-methods
    """
    Exception raised when trying to add a player to a game that has already
    started.

    Attributes:
        message - explanation of the error
    """

    def __init__(self, message):
        self.message = message
# }}}

# GameNotStarted {{{
class GameNotStarted(IntegrityError): #pylint: disable=too-few-public-methods
    """
    Exception raised when trying to do something to a game that has not
    started, but should have.

    Attributes:
        message - explanation of the error
    """

    def __init__(self, message):
        self.message = message
# }}}

# WaitForPlayers {{{
class WaitForPlayers(IntegrityError): #pylint: disable=too-few-public-methods
    """
    Exception raised when not all players have finished a task that they need
    to finish in order for the game to progress.

    Attributes:
        message - explanation of the error
    """

    def __init__(self, message):
        self.message = message
#}}}

# NameTaken {{{
class NameTaken(IntegrityError): #pylint: disable=too-few-public-methods
    """
    Raised when a player's name is not unique to the game they're playing.
    """

    def __init__(self, message):
        self.message = message
# }}}
