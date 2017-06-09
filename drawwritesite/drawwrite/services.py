# Imports {{{
import logging
from sys import exc_info

from .models import Chain, DrawLink, Game, Player, WriteLink

from django.db import transaction
from django.db import IntegrityError
# }}}

LOG = logging.getLogger(__name__)

# newGame {{{
@transaction.atomic
def newGame(name):
    """
    Return a new game with name set to the passed name.
    """
    LOG.debug('creating new game')
    gamesWithSameName = Game.objects.filter(
            name=name
        ).filter(
            started=False
        )
    if len(gamesWithSameName) > 0:
        raise GameCurrentlyBeingMade('Someone else is currently making a game with that name')
    try:
        ret = Game(name=name)
        ret.save()
    except BaseException as e:
        LOG.error('Exception while creating game: {}'.format(e))
        raise
    LOG.debug('saved new game')
    return ret
# }}}

# startGame {{{
@transaction.atomic
def startGame(game):
    """
    Set the game's 'started' attribute to True.
    """
    LOG.debug('starting game {0}'.format(game.pk))
    game.started = True
    game.save()
    LOG.debug('saved game {0}'.format(game.pk))
    return
# }}}

# playerFinished {{{
@transaction.atomic
def playerFinished(player):
    LOG.debug('increasing the number of finished players for game {0}'.format(player.game.pk))

    # Make sure the game has started.
    if not player.game.started:
        raise GameNotStarted('The game must have started for a player to complete a round')

    # Make sure the number of players who have finished isn't greater then the
    # number of players in the game.
    if player.game.numFinishedCurrentRound >= player.game.numPlayers:
        raise IntegrityError('Too many players have completed the current round')

    # Make sure that the user isn't trying to finish a round that they've
    # already finished.
    if not player.currentRound == player.game.roundNum:
        raise IntegrityError('A players round is not in sync with the game round')

    # Add one to the player's round.
    player.currentRound += 1
    player.save()

    # Add one to the number of players who have finished the current round.
    player.game.numFinishedCurrentRound += 1
    player.game.save()

    # Check if the round is complete.
    if player.game.numFinishedCurrentRound == player.game.numPlayers:
        nextRound(player.game)

    LOG.debug('increased numFinishedCurrentRound for game {0}'.format(player.game.pk))
# }}}

# nextRound {{{
@transaction.atomic
def nextRound(game):
    """
    Take a game to it's next round.
    """
    LOG.debug('increasing round for game {0}'.format(game.pk))

    # Make sure the game has started.
    if not game.started:
        raise GameNotStarted('You cannot increase the round of an unstarted game')

    # Make sure the number of players who have completed the current round
    # equals the number of players in the game.
    if not game.numPlayers == game.numFinishedCurrentRound:
        raise WaitForPlayers('Not all players have completed the current round')

    # Increase the round, set numPlayersFinishedCurrentRound to 0.
    game.roundNum += 1
    game.numFinishedCurrentRound = 0
    game.save()

    LOG.debug('round increased for game {0}'.format(game.pk))
# }}}

# newPlayer {{{
@transaction.atomic
def newPlayer(game, name, wasCreator):
    """
    Return a new player for the passed game and increase the game's number
    of players.
    """
    LOG.debug('creating new player with name {0}'.format(name))
    if game.started:
        LOG.error(' '.join((
            'attempted to add a player to a game that had already started',
        )))
        raise GameAlreadyStarted('attempted to add player to started game')
    # Get other players in this game with the same name.
    playersSameGameSameName = Player.objects.filter(
            game=game
        ).filter(
            name=name
        )
    if len(playersSameGameSameName) > 0:
        LOG.error('tried to add player with non-unique name to game')
        raise NameTaken('name {0} has been taken for this game'.format(name))
    ret = Player(game=game, position=game.numPlayers, name=name,
            wasCreator=wasCreator)
    ret.save()
    LOG.debug('saved player')
    game.numPlayers += 1
    game.save()
    LOG.debug('increased game numPlayers by 1')
    return ret
# }}}

# newChain {{{
@transaction.atomic
def newChain(player):
    """
    Create a new chain for the given user.
    """
    LOG.debug('creating new player')
    ret = Chain(player=player)
    ret.save()
    LOG.debug('saved new player')
    return ret
# }}}

# newDrawLink {{{
@transaction.atomic
def newDrawLink(chain, fileObj, addedBy):
    """
    Return a new draw link for the passed chain, or None if the next link
    for the passed chain shouldn't be a draw link.
    """
    LOG.debug('creating new draw link')
    if 0 == chain.nextLinkPosition % 2:
        LOG.error('attempted to create draw link at an invalid position')
        return None
    ret = DrawLink(f=fileObj, linkPosition=chain.nextLinkPosition,
            chain=chain, addedBy = addedBy)
    ret.save()
    LOG.debug('saved new draw link')
    chain.nextLinkPosition += 1
    chain.save()
    LOG.debug('increased chain link position')
    return ret
# }}}

# newWriteLink {{{
@transaction.atomic
def newWriteLink(chain, text, addedBy):
    """
    Return a new write link for the passed chain, or None if the next link
    for the passed chain shouldn't be a write link.
    """
    LOG.debug('creating new write link')
    if 1 == chain.nextLinkPosition % 2:
        LOG.error('attempted to create write link in invalid position')
        return None
    ret = WriteLink(text=text, linkPosition=chain.nextLinkPosition,
            chain=chain, addedBy=addedBy)
    ret.save()
    LOG.debug('saved new write link')
    chain.nextLinkPosition += 1
    chain.save()
    LOG.debug('increased chain link position')
    return ret
# }}}

# GameCurrentlyBeingMade {{{
class GameCurrentlyBeingMade(IntegrityError):
    """
    Exception raised when trying to create a game that currently exists in
    the 'not started' state.
    """

    def __init__(self, message):
        self.message = message
# }}}

# GameAlreadyStarted {{{
class GameAlreadyStarted(IntegrityError):
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
class GameNotStarted(IntegrityError):
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
class WaitForPlayers(IntegrityError):
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
class NameTaken(IntegrityError):
    """
    Raised when a player's name is not unique to the game they're playing.
    """

    def __init__(self, message):
        self.message = message
# }}}
