"""Configure the drawwrite admin page."""

from django.contrib import admin

from .models import Chain, DrawLink, Game, Player, WriteLink

def get_game_name_from_chain(chain):
    """Return the name of the game that chain belongs to."""
    return chain.player.game.name
get_game_name_from_chain.short_description = 'Game Name'

class DrawLinkInline(admin.StackedInline):
    """Configure the inline DrawLinks."""
    model = DrawLink
    extra = 0

class WriteLinkInline(admin.StackedInline):
    """Configure the inline WriteLinks view."""
    model = WriteLink
    extra = 0

class ChainAdmin(admin.ModelAdmin):
    """Configure the top level Chain view."""
    inlines = [WriteLinkInline, DrawLinkInline]
    list_display = (
        get_game_name_from_chain,
        'player',
        'next_link_position',
        'time_created',
    )
    readonly_fields = ('pk',)

class PlayerAdmin(admin.ModelAdmin):
    """Configure the top level Player view."""
    readonly_fields = ('pk',)

class PlayerInline(admin.StackedInline):
    """Configure the inline Player view."""
    model = Player
    extra = 0
    readonly_fields = ('pk',)

class GameAdmin(admin.ModelAdmin):
    """Configure the top level Game view."""
    inlines = [PlayerInline]
    readonly_fields = ('pk',)

admin.site.register(Game, GameAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(Chain, ChainAdmin)
