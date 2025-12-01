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
            f.render.return_value = MagicMock(get_width=MagicMock(return_value=100),
                                             get_height=MagicMock(return_value=20))
            return f

    class event:
        QUIT = 1
        VIDEORESIZE = 2
        MOUSEBUTTONDOWN = 3
        MOUSEMOTION = 4
        MOUSEBUTTONUP = 5
        KEYDOWN = 6

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

# Inject mock into sys.modules
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
    """Reset the board and global state before each test."""
    game_module.board_state.clear()
    game_module.move_history.clear()
    game_module.turn = 0
    game_module.selected_piece = None
    game_module.player1_user = None
    game_module.player2_user = None
    game_module.current_user = None
    game_module.game_over = False
    game_module.game_winner = None
    yield
    game_module.board_state.clear()

@pytest.fixture
def mock_filesystem():
    """Mock file operations for users and game saves."""
    hashed_pass = game_module.hash_password("testpass")
    MOCK_USERS = {
        "testuser": hashed_pass,
        "p1_user": game_module.hash_password("pass"),
        "p2_user": game_module.hash_password("pass")
    }

    users_data = json.dumps(MOCK_USERS)
    replay_data = json.dumps({"white_player": "A", "black_player": "B", "moves": ["a3-b4"]})

    def fake_open(filename, mode='r'):
        if filename == 'test_users.json':
            if 'r' in mode: return mock_open(read_data=users_data)()
            if 'w' in mode: return mock_open()()
        elif filename.startswith("games/"):
            if 'r' in mode: return mock_open(read_data=replay_data)()
            if 'w' in mode: return mock_open()()
        raise FileNotFoundError(f"No file {filename}")

    with patch("builtins.open", new=fake_open), \
         patch.object(game_module, "USERS_FILE", "test_users.json"), \
         patch("os.path.exists", return_value=True), \
         patch("os.makedirs"), \
         patch("datetime.datetime") as mock_dt:

        mock_dt.now.return_value.strftime.return_value = "2025-10-27_12-00-00"
        yield

# -----------------------------
# 4. Test Class
# -----------------------------
class TestPenguinCheckers:

    WHITE = game_module.WHITE
    BLACK = game_module.BLACK

    # --- Login/Registration ---
    def test_user_registration_and_login(self, mock_filesystem):
        game_module.load_users()
        ok, msg = game_module.verify_login("testuser", "wrongpass")
        assert not ok
        assert msg == "Incorrect password."

        ok, msg = game_module.verify_login("testuser", "testpass")
        assert ok
        assert msg == "Login successful!"

    # --- AI Turn Advancement ---
    def test_apply_ai_move_advances_turn(self, clean_board):
        game_module.create_starting_pieces()
        black_piece = game_module.piece_at(2, 1)
        target = (3, 0)

        class MockAI:
            def pick_move(self):
                black_piece.update_location(game_module.board_to_pixel(*target))
                return black_piece, target

        game_module.turn = 1
        initial_turn = game_module.turn
        game_module.apply_ai_move(MockAI())
        assert game_module.turn == initial_turn + 1

    # --- Game Record Save ---
    def test_save_game_record(self, mock_filesystem, clean_board):
        game_module.move_history = ["a3-b4", "h6-g5"]
        game_module.player1_user = "p1_user"
        game_module.player2_user = "p2_user"
        game_module.current_user = "p1_user"

        MOCK_GAME_FILE = "games/p1_user_2025-10-27_12-00-00.json"
        game_module.save_game_record()

    # --- Replay Load & Apply Move ---
    def test_load_replay_file_and_apply_move(self, mock_filesystem, clean_board):
        game_module.load_replay_file("test_game.json")
        assert game_module.replay_total == 1

        game_module.create_starting_pieces()
        white_piece_orig = game_module.piece_at(5, 0)
        game_module.apply_replay_move("a3-b4")
        piece_at_new = game_module.piece_at(4, 1)

        assert piece_at_new is not None
        assert piece_at_new == white_piece_orig
