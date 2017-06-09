from django.contrib import admin

from .models import Chain, DrawLink, Game, Player, WriteLink

class DrawLinkInline(admin.StackedInline):
    model = DrawLink
    extra = 0

class WriteLinkInline(admin.StackedInline):
    model = WriteLink
    extra = 0

class ChainAdmin(admin.ModelAdmin):
    inlines = [WriteLinkInline, DrawLinkInline]
    list_display = ('getGameName', 'player', 'nextLinkPosition', 'timeCreated',)
    readonly_fields=('pk',)

    def getGameName(self, obj):
        return obj.player.game
    getGameName.short_description = 'Game Name'

class PlayerAdmin(admin.ModelAdmin):
    readonly_fields=('pk',)

class PlayerInline(admin.StackedInline):
    model = Player
    extra = 0
    readonly_fields=('pk',)

class GameAdmin(admin.ModelAdmin):
    inlines = [PlayerInline]
    readonly_fields=('pk',)

admin.site.register(Game, GameAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(Chain, ChainAdmin)
