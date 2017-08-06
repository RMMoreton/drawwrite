#pylint: disable=invalid-name,no-self-use
"""The tests for DrawWrite."""

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
    """Tests for manipulation of Games."""

    def test_game_creation_is_successful(self):
        """
        Creating a game should work.
        """
        game = services.new_game(name='test')
        self.assertIsInstance(game, Game)

    def test_game_creation_repeated_name_is_unsuccessful(self):
        """
        Creating a game with the same name as one already created should
        raise an exception.
        """
        name = 'test'
        services.new_game(name=name)
        second_game = services.new_game(name=name)
        self.assertIsInstance(second_game, None)

    def test_game_creation_has_not_started(self):
        """
        Games should be created in the 'not started' state.
        """
        game = services.new_game(name='test')
        self.assertIs(game.started, False)

    def test_default_timeCreated_is_valid_time(self):
        """
        Creating a game with no specified 'created time' should yield a
        game with a valid 'created time' anyway.
        """
        game = services.new_game(name='test')
        self.assertIsInstance(game.time_created, datetime.datetime)

    def test_default_numPlayers_is_zero(self):
        """
        Creating a game should set the default numPlayers to zero.
        """
        game = services.new_game(name='test')
        self.assertEqual(game.num_players, 0)

    def test_cannot_create_player_for_started_game(self):
        """
        Creating a player for a started game should throw a
        GameAlreadyStarted exception.
        """
        game = services.new_game(name='test')
        game.started = True
        with self.assertRaises(services.GameAlreadyStarted):
            services.new_player(game, 'test player', True)

    def test_create_new_player_returns_valid_player(self):
        """
        Creating a player in a game should return a valid player.
        """
        game = services.new_game(name='test')
        player = services.new_player(game, 'test player', True)
        self.assertIsInstance(player, Player)

    def test_create_new_player_increases_numPlayers(self):
        """
        Creating a new player should increase numPlayers by one.
        """
        game = services.new_game(name='test')
        old = game.num_players
        services.new_player(game, 'test player', True)
        self.assertEqual(old + 1, game.num_players)

    def test_create_new_player_sets_name_correctly(self):
        """
        Creating a new player should return a player with the correct name.
        """
        name = 'test name'
        game = services.new_game(name='test')
        player = services.new_player(game, name, True)
        self.assertEqual(name, player.name)

    def test_create_new_player_inserts_foreign_key_correctly(self):
        """
        Creating a player should return a player with the 'game' field
        set to the game on which newPlayer was called.
        """
        game = services.new_game(name='test')
        player = services.new_player(game, 'test player', True)
        self.assertEqual(player.game, game)

    def test_create_new_player_sets_position_correctly(self):
        """
        Creating a player should return a player with the 'position' field
        set correctly.
        """
        game = services.new_game(name='test')
        pos = game.num_players
        player = services.new_player(game, 'test player', True)
        self.assertEqual(player.position, pos)

    def test_create_multiple_players_sets_position_correctly(self):
        """
        Creating multiple players should return players with increasing
        'position' fields.
        """
        game = services.new_game(name='test')
        num = 5
        player = None
        for i in range(num):
            player = services.new_player(game, 'test player {0}'.format(i), True)
            self.assertEqual(player.position, i)
        self.assertEqual(game.num_players, num)

    def test_create_two_players_with_same_name_in_same_game_errors(self):
        """
        Creating two players with the same name in the same game should
        cause an exception.
        """
        game = services.new_game(name='test')
        name = 'test player'
        services.new_player(game, name, True)
        with self.assertRaises(IntegrityError):
            services.new_player(game, name, True)
# }}}

# ChainTests {{{
class ChainTests(TestCase):
    """Tests for manipulating chains."""

    def get_mocked_file(self):
        """
        Get a mocked file to read from.
        """
        return SimpleUploadedFile('test.jpg', 'file contents!'.encode('utf-8'))

    def get_mocked_storage(self):
        """
        Get a mocked storage system.
        """
        return mock.MagicMock(spec=Storage, name='StorageMock')

    def test_chain_creation_is_successful(self):
        """
        Creating a chain should work.
        """
        game = services.new_game(name='test')
        player = services.new_player(game, 'test player', True)
        chain = services.new_chain(player)
        self.assertIsInstance(chain, Chain)

    def test_default_timeCreated_is_valid_time(self):
        """
        Creating a Chain with no arguments should yield a valid
        datetime.datetime in timeCreated.
        """
        game = services.new_game(name='test')
        player = services.new_player(game, 'test player', True)
        chain = services.new_chain(player)
        self.assertIsInstance(chain.time_created, datetime.datetime)

    def test_default_timeCreated_is_recent(self):
        """
        Creating a Chain with no arguments should yield a chain with
        timeCreated being in the very recent past.
        """
        game = services.new_game(name='test')
        player = services.new_player(game, 'test player', True)
        pre_creation = timezone.now()
        chain = services.new_chain(player)
        post_creation = timezone.now()
        self.assertIs(pre_creation < chain.time_created, True)
        self.assertIs(post_creation > chain.time_created, True)

    def test_default_nextLinkPosition_is_zero(self):
        """
        Creating a Chain with no arguments should yield a chain with
        nextLinkPosition of zero.
        """
        game = services.new_game(name='test')
        player = services.new_player(game, 'test player', True)
        chain = services.new_chain(player)
        self.assertEqual(chain.next_link_position, 0)

    def test_newDrawLink_with_even_nextLinkPosition_returns_None(self):
        """
        Calling newDrawLink() should return None when the chain's
        nextLinkPosition is an even number.
        """
        with mock.patch('django.core.files.storage.default_storage._wrapped',
                        self.get_mocked_storage()):
            game = services.new_game(name='test')
            player = services.new_player(game, 'test player', True)
            chain = services.new_chain(player)
            self.assertIs(services.new_draw_link(chain, self.get_mocked_file(), player), None)
            chain.next_link_position = 26
            self.assertIs(services.new_draw_link(chain, self.get_mocked_file(), player), None)

    def test_newDrawLink_with_odd_nextLinkPosition_returns_DrawLink(self):
        """
        Calling newDrawLink() should return a new DrawLink object when
        nextLinkPosition is an even number.
        """
        with mock.patch('django.core.files.storage.default_storage._wrapped',
                        self.get_mocked_storage()):
            game = services.new_game(name='test')
            player = services.new_player(game, 'test player', True)
            chain = services.new_chain(player)
            chain.next_link_position = 1
            self.assertIsInstance(services.new_draw_link(chain, self.get_mocked_file(), player),
                                  DrawLink)
            chain.next_link_position = 27
            self.assertIsInstance(services.new_draw_link(chain, self.get_mocked_file(), player),
                                  DrawLink)

    def test_newDrawLink_with_even_nextLinkPosition_does_not_increase_nextLinkPosition(self):
        """
        Calling newDrawLink() should not increase nextLinkPosition if
        nextLinkPosition is even.
        """
        with mock.patch('django.core.files.storage.default_storage._wrapped',
                        self.get_mocked_storage()):
            game = services.new_game(name='test')
            player = services.new_player(game, 'test player', True)
            chain = services.new_chain(player)
            services.new_draw_link(chain, self.get_mocked_file(), player)
            self.assertEqual(chain.next_link_position, 0)
            chain.next_link_position = 26
            services.new_draw_link(chain, self.get_mocked_file(), player)
            self.assertEqual(chain.next_link_position, 26)

    def test_newDrawLink_with_odd_nextLinkPosition_inceases_nextLinkPosition(self):
        """
        Calling newDrawLink() should increase nextLinkPosition if
        nextLinkPosition is odd.
        """
        with mock.patch('django.core.files.storage.default_storage._wrapped',
                        self.get_mocked_storage()):
            game = services.new_game(name='test')
            player = services.new_player(game, 'test player', True)
            chain = services.new_chain(player)
            chain.next_link_position = 1
            services.new_draw_link(chain, self.get_mocked_file(), player)
            self.assertEqual(chain.next_link_position, 2)
            chain.next_link_position = 27
            services.new_draw_link(chain, self.get_mocked_file(), player)
            self.assertEqual(chain.next_link_position, 28)

    def test_newDrawLink_creates_DrawLink_with_correct_linkPosition(self):
        """
        Calling newDrawLink() when nextLinkPosition is odd should create
        a DrawLink with the previous value of nextLinkPosition.
        """
        with mock.patch('django.core.files.storage.default_storage._wrapped',
                        self.get_mocked_storage()):
            game = services.new_game(name='test')
            player = services.new_player(game, 'test player', True)
            chain = services.new_chain(player)
            chain.next_link_position = 1
            expect = chain.next_link_position
            draw_link = services.new_draw_link(chain, self.get_mocked_file(), player)
            self.assertEqual(expect, draw_link.link_position)
            chain.next_link_position = 27
            expect = chain.next_link_position
            draw_link = services.new_draw_link(chain, self.get_mocked_file(), player)
            self.assertEqual(expect, draw_link.link_position)

    def test_newWriteLink_with_even_nextLinkPosition_returns_WriteLink(self):
        """
        Calling newWriteLink() should return a WriteLink if nextLinkPosition
        is an even number.
        """
        game = services.new_game(name='test')
        player = services.new_player(game, 'test player', True)
        chain = services.new_chain(player)
        self.assertIsInstance(services.new_write_link(chain, 'fake text', player), WriteLink)
        chain.next_link_position = 26
        self.assertIsInstance(services.new_write_link(chain, 'fake text', player), WriteLink)

    def test_newWriteLink_with_odd_nextLinkPosition_returns_None(self):
        """
        Calling newWriteLink() should return None if nextLinkPosition is an
        odd number.
        """
        game = services.new_game(name='test')
        player = services.new_player(game, 'test player', True)
        chain = services.new_chain(player)
        chain.next_link_position = 1
        self.assertIs(services.new_write_link(chain, 'fake text', player), None)
        chain.next_link_position = 27
        self.assertIs(services.new_write_link(chain, 'fake text', player), None)

    def test_newWriteLink_with_even_nextLinkPosition_increases_nextLinkPosition(self):
        """
        Calling newWriteLink() should increase nextLinkPosition if nextLinkPosition
        is even.
        """
        game = services.new_game(name='test')
        player = services.new_player(game, 'test player', True)
        chain = services.new_chain(player)
        services.new_write_link(chain, 'fake text', player)
        self.assertEqual(chain.next_link_position, 1)
        chain.next_link_position = 26
        services.new_write_link(chain, 'fake text', player)
        self.assertEqual(chain.next_link_position, 27)

    def test_newWriteLink_with_odd_nextLinkPosition_does_not_increase_nextLinkPosition(self):
        """
        Calling newWriteLink() should not increase nextLinkPosition if nextLinkPosition
        is odd.
        """
        game = services.new_game(name='test')
        player = services.new_player(game, 'test player', True)
        chain = services.new_chain(player)
        chain.next_link_position = 1
        services.new_write_link(chain, 'fake text', player)
        self.assertEqual(chain.next_link_position, 1)
        chain.next_link_position = 27
        services.new_write_link(chain, 'fake text', player)
        self.assertEqual(chain.next_link_position, 27)

    def test_newWriteLink_creates_WriteLink_with_correct_linkPosition(self):
        """
        Calling newWriteLink() when nextLinePosition is even should create a
        WriteLink with the previous value of nextLinePosition.
        """
        game = services.new_game(name='test')
        player = services.new_player(game, 'test player', True)
        chain = services.new_chain(player)
        expect = chain.next_link_position
        write_link = services.new_write_link(chain, 'fake text', player)
        self.assertEqual(expect, write_link.link_position)
        chain.next_link_position = 26
        expect = chain.next_link_position
        write_link = services.new_write_link(chain, 'fake text', player)
        self.assertEqual(expect, write_link.link_position)
# }}}

# IndexFormTests {{{
class IndexFormTests(TestCase):
    """Tests for the form that collects initial player data."""

    valid_data = ['lower', 'UPPER', 'miXEDcaSE',
                  'abcdefghijklmnopqrstuvwxyz1234567890_-',
                  '-_0987654321zyxwvutsrqponmlkjihgfedcba',
                 ]

    invalid_data = ['simple*', 'this$is*bad', '`', '\'', '"', '=+',
                    '<script>alert("hi!");</script>',
                   ]

    def test_form_accepts_valid_input(self):
        """
        Forms with data that contains only letters, numbers, and spaces
        should be valid.
        """
        for test_case in self.valid_data:
            form = IndexForm(data={
                'gamename': test_case,
                'username': test_case,
            })
            try:
                self.assertIs(form.is_valid(), True)
            except AssertionError:
                raise Exception('input: {0}'.format(test_case))

    def test_form_discards_invalid_input(self):
        """
        Forms with data that contains anything other then letters, numbers,
        and spaces shouldn't be valid.
        """
        for test_case in self.invalid_data:
            form = IndexForm(data={
                'gamename': test_case,
                'username': test_case,
            })
            try:
                self.assertIs(form.is_valid(), False)
            except AssertionError:
                raise Exception('input: {0}'.format(test_case))
# }}}
