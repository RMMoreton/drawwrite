"""The forms used by DrawWrite."""

import logging

from django import forms
from django.core.validators import validate_slug

from drawwrite.models import Game

LOG = logging.getLogger(__name__)

class CreateGameForm(forms.Form):
    """
    Allows the user to create a game with whatever name they want.
    """
    username = forms.CharField(label='Your Name', max_length=50,
                               validators=[validate_slug])
    gamename = forms.CharField(label='Game Name', max_length=50,
                               validators=[validate_slug])


class JoinGameForm(forms.Form):
    """
    Allows the user to join a game by inputing their name and selecing a
    game name from a dropdown.
    """
    username = forms.CharField(label='Your Name', max_length=50,
                               validators=[validate_slug])
    
    def __init__(self, *args, **kwargs):
        """
        Grab the list of avaliable games to join and set the picklist to include
        all of them.
        """
        super(JoinGameForm, self).__init__(*args, **kwargs)
        self.fields['gamename'] = forms.ChoiceField(
            label='Available Games',
            choices=get_available_games,
            validators=[validate_slug],
            required=True,
        )

def get_available_games():
    """Get a list of games that are available to join."""
    games = Game.objects.filter(started=False) #pylint: disable=no-member
    if len(games) == 0:
        options = [('', '- None -')]
    else:
        options = [('', '- Select -')]
    for game in games:
        options.append((game.name, game.name))
    return options
