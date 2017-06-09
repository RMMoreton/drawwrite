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
    game = models.ForeignKey('Game', on_delete=models.CASCADE)
    position = models.SmallIntegerField('Position')
    wasCreator = models.BooleanField('Created game')
    currentRound = models.SmallIntegerField('Current Round', default=0)

    class Meta:
        unique_together = (("name", "game"))

    def __str__(self):
        return self.name

class DrawLink(models.Model):
    """
    A DrawLink holds data for a single 'draw' step of a DrawWrite game.
    """
    f = models.FileField('File')
    linkPosition = models.SmallIntegerField('Link Position')
    chain = models.ForeignKey('Chain', on_delete=models.CASCADE)
    addedBy = models.ForeignKey('Player', on_delete=models.CASCADE)

class WriteLink(models.Model):
    """
    A WriteLink holds data for a single 'write' step of a DrawWrite game.
    """
    text = models.TextField('Description')
    linkPosition = models.SmallIntegerField('Link Position')
    chain = models.ForeignKey('Chain', on_delete=models.CASCADE)
    addedBy = models.ForeignKey('Player', on_delete=models.CASCADE)

class Chain(models.Model):
    """
    A Chain is used to connect WriteLinks and DrawLinks. It keeps track
    of how many links it has, and allows for the creation of new links
    via the newDrawLink and newWriteLink functions.
    """
    timeCreated = models.DateTimeField('Time Created', default=timezone.now)
    nextLinkPosition = models.SmallIntegerField('Next Link Position', default=0)
    player = models.OneToOneField('Player', Player)
