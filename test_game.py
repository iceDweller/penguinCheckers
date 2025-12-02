# test_game.py
import sys
import json
import pytest
from unittest.mock import MagicMock, patch, mock_open

# -----------------------------
# 1. Headless Pygame Mock
# -----------------------------

class MockPygame:
    RESIZABLE = 10
    K_BACKSPACE = 8
    K_RETURN = 13

    def init(self): pass
    def quit(self): pass

    class display:
        @staticmethod
        def set_mode(size, flags=0): return MagicMock()
        @staticmethod
        def set_caption(title): pass
        @staticmethod
        def flip(): pass
        @staticmethod
        def Info():
            mock_info = MagicMock()
            mock_info.current_w = 800
            mock_info.current_h = 800
            return mock_info

    class mouse:
        @staticmethod
        def get_pos():
            return (0, 0)

    class image:
        @staticmethod
        def load(file):
            surf = MagicMock()
            surf.convert_alpha.return_value = surf
            return surf

    class transform:
        @staticmethod
        def smoothscale(surface, size): return MagicMock()

    class time:
        @staticmethod
        def Clock(): return MagicMock()

    class font:
        @staticmethod
        def SysFont(name, size):
            f = MagicMock()
            surf = MagicMock()
            surf.get_width.return_value = 100
            surf.get_height.return_value = 20
            f.render.return_value = surf
            return f

    class event:
        QUIT = 1
        VIDEORESIZE = 2
        MOUSEBUTTONDOWN = 3
        MOUSEMOTION = 4
        MOUSEBUTTONUP = 5
        KEYDOWN = 6

        @staticmethod
        def get():
            return []

    @staticmethod
    def Rect(*args):
        rect = MagicMock()
        rect.collidepoint.return_value = False
        return rect

    class draw:
        @staticmethod
        def rect(screen, color, rect, width=0): pass
        @staticmethod
        def circle(screen, color, center, radius, width=0): pass

    @staticmethod
    def Surface(size): return MagicMock()

# Inject mock into sys.modules BEFORE importing your game
sys.modules['pygame'] = MockPygame()
sys.modules['pygame.locals'] = MagicMock()

# -----------------------------
# 2. Import the main game module
# -----------------------------
import main as game_module

# -----------------------------
# 3. Pytest Fixtures
# -----------------------------
@pytest.fixture
def clean_board():
    """
    Reset the board and relevant globals before each test.
    Uses reset_game(), and clears game_moves / board_state.
    """
    if hasattr(game_module, "game_moves"):
        game_module.game_moves.clear()
    if hasattr(game_module, "move_history"):
        game_module.move_history.clear()

    game_module.board_state.clear()
    game_module.turn = 0
    game_module.selected_piece = None
    game_module.game_over = False
    game_module.game_winner = None
    game_module.current_user = None
    yield
    game_module.board_state.clear()


@pytest.fixture
def mock_filesystem():
    """
    Mock file operations for:
      - USERS_FILE  (test_users.json)
      - replays.json (for replay list)
    """
    hashed_pass = game_module.hash_password("testpass")
    MOCK_USERS = {
        "testuser": hashed_pass,
        "p1_user": game_module.hash_password("pass"),
        "p2_user": game_module.hash_password("pass")
    }

    users_data = json.dumps(MOCK_USERS)

    # A minimal replays.json with one game: a3-b4 for White
    replays_data = json.dumps({
        "games": [
            {
                "players": {"white": "A", "black": "B"},
                "moves": [
                    {
                        "turn": 0,
                        "piece_color": "W",
                        "move": "a3-b4",
                        "king": False
                    }
                ],
                "winner": "White",
                "timestamp": 0
            }
        ]
    })

    def fake_open(filename, mode='r', *args, **kwargs):
        # Users file
        if filename == "test_users.json":
            if 'r' in mode:
                return mock_open(read_data=users_data)()
            if 'w' in mode:
                return mock_open()()
        # Replays file
        if filename == "replays.json":
            if 'r' in mode:
                return mock_open(read_data=replays_data)()
            if 'w' in mode:
                # For save_game_record writes
                return mock_open()()

        # Any other file: behave like it doesn't exist
        raise FileNotFoundError(f"No file {filename}")

    with patch("builtins.open", new=fake_open), \
         patch.object(game_module, "USERS_FILE", "test_users.json"), \
         patch("os.path.exists", return_value=True), \
         patch("os.makedirs"), \
         patch("time.time", return_value=0):
        yield


# -----------------------------
# 4. Tests
# -----------------------------
class TestPenguinCheckers:

    WHITE = game_module.WHITE
    BLACK = game_module.BLACK

    # --- Login / Registration ---
    def test_user_registration_and_login(self, mock_filesystem):
        # Wrong password
        ok, msg = game_module.verify_login("testuser", "wrongpass")
        assert not ok
        assert msg == "Incorrect password."

        # Correct password
        ok, msg = game_module.verify_login("testuser", "testpass")
        assert ok
        assert msg == "Login successful!"

    # --- AI Turn Advancement ---
    def test_apply_ai_move_advances_turn(self, clean_board):
        # Initialize a normal starting board
        game_module.reset_game()

        # Use real easy AI – just need to see turn increment
        ai = game_module.easy_AI(self.WHITE)

        initial_turn = game_module.turn
        game_module.apply_ai_move(ai)

        assert game_module.turn == initial_turn + 1

    # --- Game Record Save (replays.json style) ---
    def test_save_game_record(self, mock_filesystem, clean_board):
        # Prepare at least one logged move
        if hasattr(game_module, "game_moves"):
            game_module.game_moves.clear()
            game_module.game_moves.append({
                "turn": 0,
                "piece_color": "W",
                "move": "a3-b4",
                "king": False
            })
        elif hasattr(game_module, "move_history"):
            game_module.move_history = ["a3-b4"]

        game_module.current_user = "p1_user"
        game_module.game_over = True
        game_module.game_winner = "White"

        # Should not raise
        game_module.save_game_record()

    # --- Replay Load & Step ---
    def test_replay_step_moves_piece(self, mock_filesystem, clean_board):
        # Load replay list from mocked replays.json
        games = game_module.load_replay_list()
        assert len(games) == 1

        # Start replay for the first game
        game_data = games[0]
        game_module.start_replay(game_data)

        # In starting position, white piece at a3 is (row 5, col 0)
        from_row, from_col = 5, 0   # a3
        to_row, to_col = 4, 1       # b4

        white_piece_orig = game_module.piece_at(from_row, from_col)
        assert white_piece_orig is not None

        # One replay step should perform a3-b4
        game_module.replay_step()

        moved_piece = game_module.piece_at(to_row, to_col)
        assert moved_piece is not None
        assert moved_piece == white_piece_orig
