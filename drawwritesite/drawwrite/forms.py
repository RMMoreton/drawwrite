"""The forms used by DrawWrite."""

import logging

from django import forms
from django.core.validators import validate_slug

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
