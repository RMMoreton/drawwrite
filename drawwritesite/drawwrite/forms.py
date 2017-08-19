"""The forms used by DrawWrite."""

import logging

from django import forms
from django.core.validators import validate_slug

from drawwrite.models import Game

LOG = logging.getLogger(__name__)

class IndexForm(forms.Form):
    """
    Allows the user to input a game name and a username that they would
    like to join/create/use.
    """
    username = forms.CharField(label='Your Name', max_length=50,
                               validators=[validate_slug])
    gamename = forms.CharField(label='Game Name', max_length=50,
                               validators=[validate_slug])

    def __init__(self, *args, **kwargs):
        """
        Grab the list of avaliable games to join and set the picklist to include
        all of them.
        """
        super(IndexForm, self).__init__(*args, **kwargs)
        self.fields['open_games'] = forms.ChoiceField(
            label='Available Games',
            choices=get_available_games,
            validators=[validate_slug],
            required=False,
        )

def get_available_games():
    """Get a list of games that are available to join."""
    games = Game.objects.filter(started=False) #pylint: disable=no-member
    options = [('', '')]
    for game in games:
        options.append((game.name, game.name))
    return options
