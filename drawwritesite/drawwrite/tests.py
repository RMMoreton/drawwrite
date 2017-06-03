# Imports {{{
import datetime
import logging
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import Storage
from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone

from .models import Chain, DrawLink, Game, Player, WriteLink
from .forms import IndexForm
from . import services
# }}}

logging.disable(logging.CRITICAL)

# GameTests {{{
class GameTests(TestCase):

    def test_game_creation_is_successful(self):
        """
        Creating a game should work.
        """
        game = services.newGame(name='test')
        self.assertIsInstance(game, Game)

    def test_game_creation_repeated_name_is_unsuccessful(self):
        """
        Creating a game with the same name as one already created should
        raise an exception.
        """
        name = 'test'
        game = services.newGame(name='test')
        with self.assertRaises(IntegrityError):
            game = services.newGame(name='test')

    def test_game_creation_has_not_started(self):
        """
        Games should be created in the 'not started' state.
        """
        game = services.newGame(name='test')
        self.assertIs(game.started, False)

    def test_default_timeCreated_is_valid_time(self):
        """
        Creating a game with no specified 'created time' should yield a
        game with a valid 'created time' anyway.
        """
        game = services.newGame(name='test')
        self.assertIsInstance(game.timeCreated, datetime.datetime)

    def test_default_numPlayers_is_zero(self):
        """
        Creating a game should set the default numPlayers to zero.
        """
        game = services.newGame(name='test')
        self.assertEqual(game.numPlayers, 0)

    def test_cannot_create_player_for_started_game(self):
        """
        Creating a player for a started game should throw a
        GameAlreadyStarted exception.
        """
        game = services.newGame(name='test')
        game.started = True
        with self.assertRaises(services.GameAlreadyStarted):
            player = services.newPlayer(game, 'test player', True)

    def test_create_new_player_returns_valid_player(self):
        """
        Creating a player in a game should return a valid player.
        """
        game = services.newGame(name='test')
        player = services.newPlayer(game, 'test player', True)
        self.assertIsInstance(player, Player)

    def test_create_new_player_increases_numPlayers(self):
        """
        Creating a new player should increase numPlayers by one.
        """
        game = services.newGame(name='test')
        old = game.numPlayers
        services.newPlayer(game, 'test player', True)
        self.assertEqual(old + 1, game.numPlayers)

    def test_create_new_player_sets_name_correctly(self):
        """
        Creating a new player should return a player with the correct name.
        """
        name = 'test name'
        game = services.newGame(name='test')
        player = services.newPlayer(game, name, True)
        self.assertEqual(name, player.name)

    def test_create_new_player_inserts_foreign_key_correctly(self):
        """
        Creating a player should return a player with the 'game' field
        set to the game on which newPlayer was called.
        """
        game = services.newGame(name='test')
        player = services.newPlayer(game, 'test player', True)
        self.assertEqual(player.game, game)

    def test_create_new_player_sets_position_correctly(self):
        """
        Creating a player should return a player with the 'position' field
        set correctly.
        """
        game = services.newGame(name='test')
        pos = game.numPlayers
        player = services.newPlayer(game, 'test player', True)
        self.assertEqual(player.position, pos)

    def test_create_multiple_players_sets_position_correctly(self):
        """
        Creating multiple players should return players with increasing
        'position' fields.
        """
        game = services.newGame(name='test')
        pos = game.numPlayers
        num = 5
        player = None
        for i in range(num):
            player = services.newPlayer(game, 'test player {0}'.format(i), True)
            self.assertEqual(player.position, i)
        self.assertEqual(game.numPlayers, num)

    def test_create_two_players_with_same_name_in_same_game_errors(self):
        """
        Creating two players with the same name in the same game should
        cause an exception.
        """
        game = services.newGame(name='test')
        name = 'test player'
        services.newPlayer(game, name, True)
        with self.assertRaises(IntegrityError):
            services.newPlayer(game, name, True)
# }}}
        
# ChainTests {{{
class ChainTests(TestCase):

    def getMockedFile(self):
        """
        Get a mocked file to read from.
        """
        return SimpleUploadedFile('test.jpg', 'file contents!'.encode('utf-8'))

    def getMockedStorage(self):
        """
        Get a mocked storage system.
        """
        return mock.MagicMock(spec=Storage, name='StorageMock')

    def test_chain_creation_is_successful(self):
        """
        Creating a chain should work.
        """
        game = services.newGame(name='test')
        player = services.newPlayer(game, 'test player', True)
        chain = services.newChain(player)
        self.assertIsInstance(chain, Chain)

    def test_default_timeCreated_is_valid_time(self):
        """
        Creating a Chain with no arguments should yield a valid
        datetime.datetime in timeCreated.
        """
        game = services.newGame(name='test')
        player = services.newPlayer(game, 'test player', True)
        chain = services.newChain(player)
        self.assertIsInstance(chain.timeCreated, datetime.datetime)

    def test_default_timeCreated_is_recent(self):
        """
        Creating a Chain with no arguments should yield a chain with
        timeCreated being in the very recent past.
        """
        game = services.newGame(name='test')
        player = services.newPlayer(game, 'test player', True)
        preCreation = timezone.now()
        chain = services.newChain(player)
        postCreation = timezone.now()
        self.assertIs(preCreation < chain.timeCreated, True)
        self.assertIs(postCreation > chain.timeCreated, True)

    def test_default_nextLinkPosition_is_zero(self):
        """
        Creating a Chain with no arguments should yield a chain with
        nextLinkPosition of zero.
        """
        game = services.newGame(name='test')
        player = services.newPlayer(game, 'test player', True)
        chain = services.newChain(player)
        self.assertEqual(chain.nextLinkPosition, 0)

    def test_newDrawLink_with_even_nextLinkPosition_returns_None(self):
        """
        Calling newDrawLink() should return None when the chain's
        nextLinkPosition is an even number.
        """
        with mock.patch('django.core.files.storage.default_storage._wrapped', self.getMockedStorage()):
            game = services.newGame(name='test')
            player = services.newPlayer(game, 'test player', True)
            chain = services.newChain(player)
            self.assertIs(services.newDrawLink(chain, self.getMockedFile()), None)
            chain.nextLinkPosition = 26
            self.assertIs(services.newDrawLink(chain, self.getMockedFile()), None)

    def test_newDrawLink_with_odd_nextLinkPosition_returns_DrawLink(self):
        """
        Calling newDrawLink() should return a new DrawLink object when
        nextLinkPosition is an even number.
        """
        with mock.patch('django.core.files.storage.default_storage._wrapped', self.getMockedStorage()):
            game = services.newGame(name='test')
            player = services.newPlayer(game, 'test player', True)
            chain = services.newChain(player)
            chain.nextLinkPosition = 1
            self.assertIsInstance(services.newDrawLink(chain, self.getMockedFile()), DrawLink)
            chain.nextLinkPosition = 27
            self.assertIsInstance(services.newDrawLink(chain, self.getMockedFile()), DrawLink)

    def test_newDrawLink_with_even_nextLinkPosition_does_not_increase_nextLinkPosition(self):
        """
        Calling newDrawLink() should not increase nextLinkPosition if
        nextLinkPosition is even.
        """
        with mock.patch('django.core.files.storage.default_storage._wrapped', self.getMockedStorage()):
            game = services.newGame(name='test')
            player = services.newPlayer(game, 'test player', True)
            chain = services.newChain(player)
            services.newDrawLink(chain, self.getMockedFile())
            self.assertEqual(chain.nextLinkPosition, 0)
            chain.nextLinkPosition = 26
            services.newDrawLink(chain, self.getMockedFile())
            self.assertEqual(chain.nextLinkPosition, 26)

    def test_newDrawLink_with_odd_nextLinkPosition_inceases_nextLinkPosition(self):
        """
        Calling newDrawLink() should increase nextLinkPosition if
        nextLinkPosition is odd.
        """
        with mock.patch('django.core.files.storage.default_storage._wrapped', self.getMockedStorage()):
            game = services.newGame(name='test')
            player = services.newPlayer(game, 'test player', True)
            chain = services.newChain(player)
            chain.nextLinkPosition = 1
            services.newDrawLink(chain, self.getMockedFile())
            self.assertEqual(chain.nextLinkPosition, 2)
            chain.nextLinkPosition = 27
            services.newDrawLink(chain, self.getMockedFile())
            self.assertEqual(chain.nextLinkPosition, 28)

    def test_newDrawLink_creates_DrawLink_with_correct_linkPosition(self):
        """
        Calling newDrawLink() when nextLinkPosition is odd should create
        a DrawLink with the previous value of nextLinkPosition.
        """
        with mock.patch('django.core.files.storage.default_storage._wrapped', self.getMockedStorage()):
            game = services.newGame(name='test')
            player = services.newPlayer(game, 'test player', True)
            chain = services.newChain(player)
            chain.nextLinkPosition = 1
            expect = chain.nextLinkPosition
            drawLink = services.newDrawLink(chain, self.getMockedFile())
            self.assertEqual(expect, drawLink.linkPosition)
            chain.nextLinkPosition = 27
            expect = chain.nextLinkPosition
            drawLink = services.newDrawLink(chain, self.getMockedFile())
            self.assertEqual(expect, drawLink.linkPosition)

    def test_newWriteLink_with_even_nextLinkPosition_returns_WriteLink(self):
        """
        Calling newWriteLink() should return a WriteLink if nextLinkPosition
        is an even number.
        """
        game = services.newGame(name='test')
        player = services.newPlayer(game, 'test player', True)
        chain = services.newChain(player)
        self.assertIsInstance(services.newWriteLink(chain, 'fake text'), WriteLink)
        chain.nextLinkPosition = 26
        self.assertIsInstance(services.newWriteLink(chain, 'fake text'), WriteLink)

    def test_newWriteLink_with_odd_nextLinkPosition_returns_None(self):
        """
        Calling newWriteLink() should return None if nextLinkPosition is an
        odd number.
        """
        game = services.newGame(name='test')
        player = services.newPlayer(game, 'test player', True)
        chain = services.newChain(player)
        chain.nextLinkPosition = 1
        self.assertIs(services.newWriteLink(chain, 'fake text'), None)
        chain.nextLinkPosition = 27
        self.assertIs(services.newWriteLink(chain, 'fake text'), None)

    def test_newWriteLink_with_even_nextLinkPosition_increases_nextLinkPosition(self):
        """
        Calling newWriteLink() should increase nextLinkPosition if nextLinkPosition
        is even.
        """
        game = services.newGame(name='test')
        player = services.newPlayer(game, 'test player', True)
        chain = services.newChain(player)
        services.newWriteLink(chain, 'fake text')
        self.assertEqual(chain.nextLinkPosition, 1)
        chain.nextLinkPosition = 26
        services.newWriteLink(chain, 'fake text')
        self.assertEqual(chain.nextLinkPosition, 27)

    def test_newWriteLink_with_odd_nextLinkPosition_does_not_increase_nextLinkPosition(self):
        """
        Calling newWriteLink() should not increase nextLinkPosition if nextLinkPosition
        is odd.
        """
        game = services.newGame(name='test')
        player = services.newPlayer(game, 'test player', True)
        chain = services.newChain(player)
        chain.nextLinkPosition = 1
        services.newWriteLink(chain, 'fake text')
        self.assertEqual(chain.nextLinkPosition, 1)
        chain.nextLinkPosition = 27
        services.newWriteLink(chain, 'fake text')
        self.assertEqual(chain.nextLinkPosition, 27)

    def test_newWriteLink_creates_WriteLink_with_correct_linkPosition(self):
        """
        Calling newWriteLink() when nextLinePosition is even should create a
        WriteLink with the previous value of nextLinePosition.
        """
        game = services.newGame(name='test')
        player = services.newPlayer(game, 'test player', True)
        chain = services.newChain(player)
        expect = chain.nextLinkPosition
        writeLink = services.newWriteLink(chain, 'fake text')
        self.assertEqual(expect, writeLink.linkPosition)
        chain.nextLinkPosition = 26
        expect = chain.nextLinkPosition
        writeLink = services.newWriteLink(chain, 'fake text')
        self.assertEqual(expect, writeLink.linkPosition)
# }}}

# IndexFormTests {{{
class IndexFormTests(TestCase):
    
    validData = ['lower', 'UPPER', 'miXEDcaSE',
            'abcdefghijklmnopqrstuvwxyz1234567890_-',
            '-_0987654321zyxwvutsrqponmlkjihgfedcba',
    ]

    invalidData = ['simple*', 'this$is*bad', '`', '\'', '"', '=+',
            '<script>alert("hi!");</script>',
    ]

    def test_form_accepts_valid_input(self):
        """
        Forms with data that contains only letters, numbers, and spaces
        should be valid.
        """
        for testCase in self.validData:
            form = IndexForm(data={
                'gamename': testCase,
                'username': testCase,
            })
            try:
                self.assertIs(form.is_valid(), True)
            except AssertionError:
                raise Exception('input: {0}'.format(testCase))

    def test_form_discards_invalid_input(self):
        """
        Forms with data that contains anything other then letters, numbers,
        and spaces shouldn't be valid.
        """
        for testCase in self.invalidData:
            form = IndexForm(data={
                'gamename': testCase,
                'username': testCase,
            })
            self.assertIs(form.is_valid(), False)
# }}}
