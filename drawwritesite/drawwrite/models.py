from django.conf import settings
from django.db import models
from django.utils import timezone
from django.db import transaction

class Game(models.Model):
    """
    Games have a number of players, a unique name, and a
    created time.
    """
    name = models.CharField('Name', max_length=50)
    numPlayers = models.SmallIntegerField('Number of Players', default=0)
    started = models.BooleanField('Started?', default=False)
    timeCreated = models.DateTimeField('Time Created', default=timezone.now)
    roundNum = models.SmallIntegerField('Current Round', default=0)
    numFinishedCurrentRound = models.SmallIntegerField(
            'Number of players who have finished the current round',
            default=0
    )

    def __str__(self):
        return self.name

class Player(models.Model):
    """
    Holds information about a user, such as their name, a reference
    to their game, and their position in the cycle.
    """
    name = models.CharField('Name', max_length=50)
    game = models.ForeignKey(Game)
    position = models.SmallIntegerField('Position')
    wasCreator = models.BooleanField('Created game')
    currentRound = models.SmallIntegerField('Current Round', default=0)

    def __str__(self):
        return self.name

class Chain(models.Model):
    """
    A Chain is used to connect WriteLinks and DrawLinks. It keeps track
    of how many links it has, and who created it.
    """
    timeCreated = models.DateTimeField('Time Created', default=timezone.now)
    nextLinkPosition = models.SmallIntegerField('Next Link Position', default=0)
    player = models.OneToOneField(Player)

    def __str__(self):
        return '{0}\'s chain'.format(self.player)

class DrawLink(models.Model):
    """
    A DrawLink holds data for a single 'draw' step of a DrawWrite game.
    """
    f = models.FileField('File')
    linkPosition = models.SmallIntegerField('Link Position')
    chain = models.OneToOneField(Chain)
    addedBy = models.ForeignKey(Player)

class WriteLink(models.Model):
    """
    A WriteLink holds data for a single 'write' step of a DrawWrite game.
    """
    text = models.TextField('Description')
    linkPosition = models.SmallIntegerField('Link Position')
    chain = models.OneToOneField(Chain)
    addedBy = models.ForeignKey(Player)
