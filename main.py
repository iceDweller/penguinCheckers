
import pygame
import time
import random
import json
import hashlib
import os
import datetime
import sqlite3

pygame.init()

################################################
# WINDOW + SCALING
################################################
UI_SPACE_HEIGHT = 60
info = pygame.display.Info()
SCREEN_WIDTH = min(info.current_w - 100, 800)
SCREEN_HEIGHT = min(info.current_h - 100, 800) + 60
last_resize_time = 0
RESIZE_DEBOUNCE_MS = 100
pending_resize = None

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Penguin Checkers")

UI_SCALE = 1.0
MENU_SCALE = 1.0

TILE_SIZE = min(SCREEN_WIDTH, SCREEN_HEIGHT - UI_SPACE_HEIGHT) // 8
BOARD_SIZE = TILE_SIZE * 8
BOARD_OFFSET_X = (SCREEN_WIDTH - BOARD_SIZE) // 2
BOARD_OFFSET_Y = UI_SPACE_HEIGHT
ROWS = 8

clock = pygame.time.Clock()

################################################
# COLORS
################################################
BLUE_TILE = (0, 102, 204)
WHITE_TILE = (255, 255, 255)

BLACK = (35, 35, 35)
WHITE = (255, 255, 255)

BLACK_BORDER = (70, 70, 70)
WHITE_BORDER = (200, 200, 200)

HIGHLIGHT_WIDTH = 5
HIGHLIGHT_YELLOW = (255, 255, 0)
HIGHLIGHT_GREEN = (0, 255, 0)
HIGHLIGHT_RED = (255, 0, 0)
HIGHLIGHT_GOLD = (255, 215, 0)

################################################
# GLOBAL GAME STATE
################################################
board_state = []
board_history = []

turn = 0
selected_piece = None
valid_moves = []
dragging = False
orig_pos = None
hover_piece = None
multi_jump = False
jump_occurred = False
game_over = False
game_winner = None
show_menu = False
drag_origin = None          # where a drag started
pending_mode = None         # "pvp", "ai_easy", "ai_hard"
game_vs_ai = False          # False = PvP, True = vs AI
game_moves = []             # list of recorded moves for replays
replay_active = False       # active replay mode flag
replay_select_active = False

################################################
# MENU BUTTON STORAGE
################################################
menu_buttons = {
    "close": None,
    "easy": None,
    "hard": None,
    "pvp": None,
    "pve": None,
    "quit": None
}

################################################
# USER ACCOUNT SYSTEM (SQLite)
################################################

DB_FILE = "users.db"

current_user = None
player1_user = None
player2_user = None

def init_db():
    """Create the users table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username      TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def hash_password(pw: str) -> str:
    """Return a SHA-256 hash of the password."""
    return hashlib.sha256(pw.encode()).hexdigest()


def register_user(username: str, password: str):
    """
    Register a new user in the SQLite DB.
    Returns (ok: bool, message: str)
    """
    if not username or not password:
        return False, "Username and password are required."

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Check if username already exists
    cur.execute("SELECT 1 FROM users WHERE username = ?", (username,))
    if cur.fetchone():
        conn.close()
        return False, "Username already exists."

    # Insert new user
    cur.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, hash_password(password))
    )
    conn.commit()
    conn.close()
    return True, "Registration successful!"


def verify_login(username: str, password: str):
    """
    Verify credentials against the SQLite DB.
    Returns (ok: bool, message: str)
    """
    if not username or not password:
        return False, "Username and password are required."

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()

    if row is None:
        return False, "User does not exist."

    if row[0] != hash_password(password):
        return False, "Incorrect password."

    return True, "Login successful!"


# Ensure the database exists when the module is imported
init_db()


################################################
# LOGIN SCREEN STATE
################################################
login_screen_active = False
register_mode = False
login_stage = "P1"        # P1 login, then P2 if needed
login_username = ""
login_password = ""
login_message = ""
input_active = None

################################################
# START MENU & GAME MODE
################################################
START_MENU_ACTIVE = True
GAME_MODE = ""   # "pvp" or "pve"
HUMAN_COLOR = WHITE
AI_COLOR = BLACK
AI_DIFFICULTY = "EASY"

################################################
# REPLAY SYSTEM STATE
################################################
replay_mode_active = False
replay_select_active = False
replay_file_select_active = False
replay_moves = []
replay_index = 0
replay_total = 0
replay_record = None
move_history = []

################################################
# PENGUIN SPRITES
################################################
BLACK_PENGUIN_BASE = None
WHITE_PENGUIN_BASE = None
BLACK_PENGUIN_KING_BASE = None
WHITE_PENGUIN_KING_BASE = None

BLACK_PENGUIN = None
WHITE_PENGUIN = None
BLACK_PENGUIN_KING = None
WHITE_PENGUIN_KING = None

try:
    BLACK_PENGUIN_BASE = pygame.image.load("BlackPenguinPiece.png").convert_alpha()
    WHITE_PENGUIN_BASE = pygame.image.load("WhitePenguinPiece.png").convert_alpha()
    BLACK_PENGUIN_KING_BASE = pygame.image.load("BlackPenguinKingPiece.png").convert_alpha()
    WHITE_PENGUIN_KING_BASE = pygame.image.load("WhitePenguinKingPiece.png").convert_alpha()
except:
    BLACK_PENGUIN_BASE = None
    WHITE_PENGUIN_BASE = None
    BLACK_PENGUIN_KING_BASE = None
    WHITE_PENGUIN_KING_BASE = None

def rescale_penguin_images():
    global BLACK_PENGUIN, WHITE_PENGUIN, BLACK_PENGUIN_KING, WHITE_PENGUIN_KING
    size = max(1, int(TILE_SIZE * 0.9))
    if BLACK_PENGUIN_BASE:
        BLACK_PENGUIN = pygame.transform.smoothscale(BLACK_PENGUIN_BASE, (size, size))
        WHITE_PENGUIN = pygame.transform.smoothscale(WHITE_PENGUIN_BASE, (size, size))
        BLACK_PENGUIN_KING = pygame.transform.smoothscale(BLACK_PENGUIN_KING_BASE, (size, size))
        WHITE_PENGUIN_KING = pygame.transform.smoothscale(WHITE_PENGUIN_KING_BASE, (size, size))
    else:
        BLACK_PENGUIN = WHITE_PENGUIN = BLACK_PENGUIN_KING = WHITE_PENGUIN_KING = None

rescale_penguin_images()

################################################
# COORDINATE CONVERSION
################################################

def board_to_pixel(row, col):
    """Convert board (row, col) to pixel center of that square."""
    x = BOARD_OFFSET_X + col * TILE_SIZE + TILE_SIZE // 2
    y = UI_SPACE_HEIGHT + row * TILE_SIZE + TILE_SIZE // 2
    return x, y


def pixel_to_board(pos):
    """Convert pixel position to board (row, col), or (-1, -1) if off-board."""
    x, y = pos
    col = int((x - BOARD_OFFSET_X) // TILE_SIZE)
    row = int((y - UI_SPACE_HEIGHT) // TILE_SIZE)
    if 0 <= col < 8 and 0 <= row < 8:
        return row, col
    return -1, -1

def board_to_screen_pixel(row, col):
    return board_to_pixel(row, col)

################################################
# CHECKER CLASS
################################################

class Checker:
    def __init__(self, location, status, player, direction):
        self.location = location
        self.status = status          # "normal" or "king"
        self.player = player          # WHITE or BLACK
        self.direction = direction    # +1 or -1 (ignored if king)
        self.king = (status == "king")
        self.radius = TILE_SIZE // 3
        self.update_rect()

    def update_rect(self):
        """Update clickable rect based on current location and radius."""
        x, y = self.location
        self.radius = TILE_SIZE // 3
        self.rect = pygame.Rect(
            x - self.radius,
            y - self.radius,
            self.radius * 2,
            self.radius * 2
        )

    def clicked(self, pos):
        """Return True if the mouse clicked on this piece."""
        return self.rect.collidepoint(pos)

    def update_location(self, new_pos):
        """Move to a new pixel location and re-check king status."""
        self.location = new_pos
        self.update_rect()
        check_king_status(self)

    def make_king(self):
        """Promote to king (used in replay and in-game)."""
        self.king = True
        self.status = "king"
        # direction is ignored for kings (get_valid_moves uses king flag)

    def draw_self(self):
        """Draw this checker as a penguin sprite if available, else a circle."""
        # If sprites are missing, fallback to plain circles
        if BLACK_PENGUIN is None or WHITE_PENGUIN is None:
            pygame.draw.circle(screen, self.player, self.location, self.radius)
            border_color = WHITE_BORDER if self.player == WHITE else BLACK_BORDER
            pygame.draw.circle(screen, border_color, self.location, self.radius, HIGHLIGHT_WIDTH)
            if self.king:
                pygame.draw.circle(screen, HIGHLIGHT_GOLD, self.location, self.radius // 2)
            return

        # choose sprite
        if self.player == WHITE:
            img = WHITE_PENGUIN_KING if self.king else WHITE_PENGUIN
        else:
            img = BLACK_PENGUIN_KING if self.king else BLACK_PENGUIN

        if img:
            rect = img.get_rect(center=self.location)
            screen.blit(img, rect)
        else:
            # super defensive fallback
            pygame.draw.circle(screen, self.player, self.location, self.radius)
            if self.king:
                pygame.draw.circle(screen, HIGHLIGHT_GOLD, self.location, self.radius // 2)

################################################
# GAME BOARD SETUP
################################################

def reset_game():
    global board_state, board_history, selected_piece, valid_moves
    global dragging, orig_pos, multi_jump, jump_occurred, turn
    global game_over, game_winner, move_history, game_moves

    board_state = []
    board_history = []
    move_history = []
    game_moves = []
    turn = 0
    selected_piece = None
    valid_moves = []
    dragging = False
    orig_pos = None
    multi_jump = False
    jump_occurred = False
    game_over = False
    game_winner = None

    for r in range(3):
        for c in range(8):
            if (r + c) % 2 == 1:
                piece = Checker(location=board_to_pixel(r, c),
                                status="normal",
                                player=BLACK,
                                direction=1)
                board_state.append(piece)

    for r in range(5, 8):
        for c in range(8):
            if (r + c) % 2 == 1:
                piece = Checker(location=board_to_pixel(r, c),
                                status="normal",
                                player=WHITE,
                                direction=-1)
                board_state.append(piece)

    save_game_state()

################################################
# REPLAY SYSTEM
################################################

def save_game_record():
    global game_moves, game_winner
    global player1_user, player2_user, HUMAN_COLOR, pending_mode

    if not game_moves:
        return

    # --- Decide who is white / black for the replay label ---
    if pending_mode == "pvp":
        # In Human vs Human, just treat Player 1 as White and Player 2 as Black
        white_player = player1_user or "Player 1"
        black_player = player2_user or "Player 2"
    else:
        # Human vs AI
        if HUMAN_COLOR == WHITE:
            white_player = player1_user or "Human"
            black_player = "AI"
        else:
            white_player = "AI"
            black_player = player1_user or "Human"

    record = {
        "players": {
            "white": white_player,
            "black": black_player,
        },
        "moves": game_moves,
        "winner": game_winner,
        "timestamp": time.time()
    }

    # --- Make sure file exists and is valid JSON ---
    if not os.path.exists("replays.json"):
        with open("replays.json", "w") as f:
            json.dump({"games": []}, f)

    try:
        with open("replays.json", "r") as f:
            data = json.load(f)
    except Exception:
        data = {"games": []}

    if "games" not in data:
        data["games"] = []

    data["games"].append(record)

    with open("replays.json", "w") as f:
        json.dump(data, f, indent=4)

def apply_replay_move():
    global replay_index, board_state, turn

    if replay_index >= replay_total:
        return

    move = replay_moves[replay_index]
    sr, sc = move["start"]
    dr, dc = move["end"]

    piece = piece_at(sr, sc)
    if not piece:
        replay_index += 1
        return

    if abs(dr - sr) == 2:
        jumped = piece_at((sr + dr) // 2, (sc + dc) // 2)
        if jumped:
            try:
                board_state.remove(jumped)
            except:
                pass

    piece.update_location(board_to_pixel(dr, dc))
    turn += 1
    replay_index += 1

################################################
# ALGEBRAIC MOVE NOTATION
################################################

def algebraic_square(r, c):
    cols = "abcdefgh"
    return f"{cols[c]}{8 - r}"

def record_move(piece, sr, sc, dr, dc, jump):
    global move_history

    move_text = ""
    if piece.player == WHITE:
        move_text += "W: "
    else:
        move_text += "B: "

    move_text += algebraic_square(sr, sc)

    if jump:
        move_text += "x"
    else:
        move_text += "-"

    move_text += algebraic_square(dr, dc)
    move_history.append(move_text)

################################################
# AI
################################################

def get_all_player_moves(player_color):
    moves = []
    forced = get_forced_jump_pieces(player_color)

    pieces = forced if forced else [p for p in board_state if p.player == player_color]
    for p in pieces:
        valid = get_valid_moves(p, only_jumps=bool(forced))
        for (r, c) in valid:
            moves.append((p, (r, c)))
    return moves


################################################
# HELPER FUNCTIONS
################################################

def piece_at(r, c):
    for p in board_state:
        pr, pc = pixel_to_board(p.location)
        if pr == r and pc == c:
            return p
    return None

def check_king_status(piece):
    r, c = pixel_to_board(piece.location)
    if piece.player == WHITE and r == 0:
        piece.king = True
    if piece.player == BLACK and r == 7:
        piece.king = True

def get_current_turn():
    return WHITE if turn % 2 == 0 else BLACK

def save_game_state():
    state = []
    for piece in board_state:
        new_piece = Checker(piece.location, piece.status, piece.player, piece.direction)
        new_piece.king = piece.king
        state.append(new_piece)

    board_history.append({
        'board': state,
        'turn': turn,
        'jump_occurred': jump_occurred,
        'multi_jump': multi_jump,
        'game_over': game_over,
        'game_winner': game_winner
    })

def on_turn_end():
    check_game_over()
    save_game_state()

################################################
# VALID MOVE LOGIC
################################################

def get_valid_moves(piece, only_jumps=False):
    moves = []
    sr, sc = pixel_to_board(piece.location)

    # King or normal direction
    directions = []
    if piece.king:
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    else:
        directions = [(piece.direction, -1), (piece.direction, 1)]

    # Check each direction
    for dr, dc in directions:
        r = sr + dr
        c = sc + dc

        # Simple move
        if not only_jumps:
            if 0 <= r < 8 and 0 <= c < 8 and piece_at(r, c) is None:
                # Only allow landing on dark tiles
                if (r + c) % 2 == 1:
                    moves.append((r, c))

        # Jump move
        jr = sr + 2 * dr
        jc = sc + 2 * dc
        if 0 <= jr < 8 and 0 <= jc < 8:
            middle = piece_at(sr + dr, sc + dc)
            if middle and middle.player != piece.player and piece_at(jr, jc) is None:
                # Must land on dark tile
                if (jr + jc) % 2 == 1:
                    moves.append((jr, jc))

    return moves

################################################
# FORCED JUMP LOGIC
################################################

def get_forced_jump_pieces(player_color):
    forced = []
    for p in board_state:
        if p.player == player_color:
            moves = get_valid_moves(p, only_jumps=True)
            if moves:
                forced.append(p)
    return forced

################################################
# GAME OVER CHECK
################################################

def check_game_over():
    global game_over, game_winner

    white_left = any(p.player == WHITE for p in board_state)
    black_left = any(p.player == BLACK for p in board_state)

    if not white_left:
        game_over = True
        game_winner = "Black"
        save_game_record()
    elif not black_left:
        game_over = True
        game_winner = "White"
        save_game_record()

    # Check moves remaining
    if not game_over:
        moves = get_all_player_moves(get_current_turn())
        if not moves:
            game_over = True
            game_winner = "White" if get_current_turn() == BLACK else "Black"
            save_game_record()

################################################
# BOARD LOGIC FOR SCALING
################################################

def scale_window(new_size):
    global SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, BOARD_SIZE
    global BOARD_OFFSET_X, BOARD_OFFSET_Y, UI_SCALE, MENU_SCALE

    SCREEN_WIDTH, SCREEN_HEIGHT = new_size
    if SCREEN_HEIGHT < 200:
        SCREEN_HEIGHT = 200
    if SCREEN_WIDTH < 200:
        SCREEN_WIDTH = 200

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)

    TILE_SIZE = min(SCREEN_WIDTH, SCREEN_HEIGHT - UI_SPACE_HEIGHT) // 8
    BOARD_SIZE = TILE_SIZE * 8
    BOARD_OFFSET_X = (SCREEN_WIDTH - BOARD_SIZE) // 2
    BOARD_OFFSET_Y = UI_SPACE_HEIGHT

    UI_SCALE = max(0.5, min(SCREEN_WIDTH / 800, SCREEN_HEIGHT / 800))
    MENU_SCALE = UI_SCALE

    rescale_penguin_images()

    for piece in board_state:
        r, c = pixel_to_board(piece.location)
        piece.update_location(board_to_pixel(r, c))

################################################
# LOGIC BOARD (debug helper)
################################################

def logic_board():
    board = [[None for _ in range(8)] for _ in range(8)]
    for p in board_state:
        r, c = pixel_to_board(p.location)
        if p.king:
            board[r][c] = ("Wk" if p.player == WHITE else "Bk")
        else:
            board[r][c] = ("W" if p.player == WHITE else "B")
    return board

################################################
# MOVEMENT EXECUTION
################################################

def execute_move(piece, sr, sc, dr, dc):
    """
    Move `piece` from (sr, sc) to (dr, dc), handle captures, log move,
    and advance the turn. Used by both human and AI moves.

    Returns:
        "continue" if a jump was made and more jumps are available
        "done"     if the turn has ended
    """
    global selected_piece, valid_moves, jump_occurred, multi_jump, turn

    # is this a jump?
    is_jump = abs(dr - sr) == 2

    # Handle capture
    if is_jump:
        jumped = piece_at((sr + dr) // 2, (sc + dc) // 2)
        if jumped and jumped in board_state:
            board_state.remove(jumped)

    # Move the piece
    piece.update_location(board_to_pixel(dr, dc))

    # Log move
    record_move(piece, sr, sc, dr, dc, is_jump)

    # Multi-jump logic
    jump_occurred = is_jump
    multi_jump = []

    if is_jump:
        # Only consider further jumps with this same piece
        multi_jump = get_valid_moves(piece, only_jumps=True)

    if multi_jump:
        # still same player's turn; keep using this piece
        selected_piece = piece
        valid_moves = multi_jump
        return "continue"

    # End of turn
    selected_piece = None
    valid_moves = []
    jump_occurred = False
    multi_jump = False
    turn += 1
    on_turn_end()
    return "done"

################################################
# DROP HANDLER
################################################

def handle_drop(selected_piece, mouse_pos):
    global dragging, valid_moves, orig_pos

    row, col = pixel_to_board(mouse_pos)
    sr, sc = pixel_to_board(orig_pos)
    dr, dc = row, col

    if (row, col) not in valid_moves:
        selected_piece.update_location(orig_pos)
        return "invalid"

    result = execute_move(selected_piece, sr, sc, dr, dc)
    return result


################################################
# EASY AI
################################################

class easy_AI:
    def __init__(self, color):
        self.color = color

    def pick_move(self):
        moves = get_all_player_moves(self.color)
        if not moves:
            return None
        return random.choice(moves)

################################################
# HARD AI
################################################

class hard_AI:
    def __init__(self, color):
        self.color = color

    def evaluate_move(self, piece, r, c):
        # Base score
        score = 0
        sr, sc = pixel_to_board(piece.location)
        dr = r - sr

        # Prefer jumps
        if abs(dr) == 2:
            score += 10

        # Prefer moving toward promotion
        if piece.player == BLACK:
            score += dr
        else:
            score -= dr

        # Promote bonus
        if piece.player == BLACK and r == 7:
            score += 50
        if piece.player == WHITE and r == 0:
            score += 50

        # Center control
        if 2 <= r <= 5 and 2 <= c <= 5:
            score += 3

        # King bonus
        if piece.king:
            score += 5

        # Slight randomness so it's not deterministic
        score += random.uniform(0, 1)

        return score

    def pick_move(self):
        moves = get_all_player_moves(self.color)
        if not moves:
            return None

        scored = []
        for piece, (r, c) in moves:
            scored.append((self.evaluate_move(piece, r, c), piece, (r, c)))

        scored.sort(reverse=True, key=lambda x: x[0])
        _, best_piece, best_move = scored[0]
        return best_piece, best_move

################################################
# AI TURN EXECUTION
################################################


def apply_ai_move(ai):
    global selected_piece, valid_moves

    # First chosen move for this turn
    move = ai.pick_move()
    if not move:
        return

    piece, (r, c) = move
    sr, sc = pixel_to_board(piece.location)

    status = execute_move(piece, sr, sc, r, c)

    # If this started a jump chain, keep jumping automatically
    while status == "continue" and not game_over:
        if not selected_piece or not valid_moves:
            break

        # Simple choice: randomly pick next jump landing square
        # (we could make this smarter later)
        next_r, next_c = random.choice(valid_moves)
        sr2, sc2 = pixel_to_board(selected_piece.location)
        status = execute_move(selected_piece, sr2, sc2, next_r, next_c)


################################################
# MOVE LOGGING
################################################

def square_to_text(r, c):
    # Convert board coordinates to algebraic notation (a1–h8)
    file = "abcdefgh"[c]
    rank = str(8 - r)
    return file + rank

def record_move(piece, sr, sc, dr, dc, is_jump):
    source = square_to_text(sr, sc)
    dest = square_to_text(dr, dc)

    notation = f"{source}x{dest}" if is_jump else f"{source}-{dest}"

    move_record = {
        "turn": turn,
        "piece_color": "W" if piece.player == WHITE else "B",
        "move": notation,
        "king": piece.king
    }

    game_moves.append(move_record)

################################################
# GAME STATE SNAPSHOT
################################################

def snapshot_board():
    snap = []
    for p in board_state:
        r, c = pixel_to_board(p.location)
        snap.append({
            "row": r,
            "col": c,
            "player": "W" if p.player == WHITE else "B",
            "king": p.king
        })
    return snap

################################################
# REPLAY LOADING
################################################

def load_replay_list():
    # Ensure file exists
    if not os.path.exists("replays.json"):
        with open("replays.json", "w") as f:
            json.dump({"games": []}, f)

    with open("replays.json", "r") as f:
        data = json.load(f)

    # Support both:
    #  - {"games": [ ... ]}
    #  - [ ... ]   (old style)
    if isinstance(data, list):
        games = data
    else:
        games = data.get("games", [])

    return games


def load_replay_game(index):
    games = load_replay_list()
    if 0 <= index < len(games):
        return games[index]
    return None

################################################
# REPLAY PLAYBACK ENGINE
################################################

replay_active = False
replay_moves = []
replay_index = 0
replay_speed = 60  # frames per move

def start_replay(game_data):
    global replay_active, replay_moves, replay_index

    moves = game_data.get("moves", [])
    if not moves:
        # no moves to replay
        replay_active = False
        return

    replay_active = True
    replay_moves = moves
    replay_index = 0

    reset_game()

# --- Manual replay helpers ---
def extract_move_token(move_entry):
    """
    Accepts multiple historical formats and returns a move token like 'c3-d4' or 'e5xf4'.

    Supported:
      - "c3-d4" (string)
      - {"move": "c3-d4", ...}
      - {"start": [sr, sc], "end": [dr, dc]}
    """
    # Already a string like "c3-d4" or "e5xf4"
    if isinstance(move_entry, str):
        return move_entry

    if isinstance(move_entry, dict):
        # New format with 'move'
        if "move" in move_entry:
            return move_entry["move"]

        # Old coordinate format
        if "start" in move_entry and "end" in move_entry:
            sr, sc = move_entry["start"]
            dr, dc = move_entry["end"]
            return f"{algebraic_square(sr, sc)}-{algebraic_square(dr, dc)}"

    # Unknown format
    return None

def apply_replay_move_index(idx):
    """Apply a single recorded move by index onto the current board."""
    if idx < 0 or idx >= len(replay_moves):
        return

    move = replay_moves[idx]
    token = extract_move_token(move)
    if not token:
        return

    # token like "c3-d4" or "e5xf4"
    src = token[:2]
    dst = token[-2:]

    sr = 8 - int(src[1])
    sc = "abcdefgh".index(src[0])
    dr = 8 - int(dst[1])
    dc = "abcdefgh".index(dst[0])

    piece = piece_at(sr, sc)
    if not piece:
        return

    # Handle capture (jump)
    if abs(dr - sr) == 2:
        jumped = piece_at((sr + dr) // 2, (sc + dc) // 2)
        if jumped and jumped in board_state:
            board_state.remove(jumped)

    # Move the piece
    piece.update_location(board_to_pixel(dr, dc))

    # Promote if needed
    if (piece.player == WHITE and dr == 0) or (piece.player == BLACK and dr == 7):
        piece.king = True

def reset_board_for_replay():
    """Reset the board to initial position, then apply moves up to replay_index."""
    global turn
    # fresh starting position
    reset_game()
    turn = 0

    for i in range(replay_index):
        apply_replay_move_index(i)
        turn += 1


def draw_replay_controls():
    font = pygame.font.SysFont(None, int(32 * UI_SCALE))

    btn_h = int(45 * UI_SCALE)
    btn_w = int(140 * UI_SCALE)
    pad = int(15 * UI_SCALE)
    top_y = pad  # place them at top of screen

    btn_prev    = pygame.Rect(pad,                     top_y, btn_w, btn_h)
    btn_next    = pygame.Rect(pad + btn_w + pad,       top_y, btn_w, btn_h)
    btn_restart = pygame.Rect(pad + (btn_w + pad)*2,   top_y, btn_w, btn_h)
    btn_exit    = pygame.Rect(pad + (btn_w + pad)*3,   top_y, btn_w, btn_h)

    # PREV
    pygame.draw.rect(screen, (100, 100, 200), btn_prev)
    pygame.draw.rect(screen, (150, 150, 255), btn_prev, 2)
    screen.blit(font.render("Prev", True, (255, 255, 255)),
                (btn_prev.centerx - 30, btn_prev.centery - 15))

    # NEXT
    pygame.draw.rect(screen, (100, 200, 100), btn_next)
    pygame.draw.rect(screen, (150, 255, 150), btn_next, 2)
    screen.blit(font.render("Next", True, (255, 255, 255)),
                (btn_next.centerx - 30, btn_next.centery - 15))

    # RESTART
    pygame.draw.rect(screen, (200, 200, 100), btn_restart)
    pygame.draw.rect(screen, (255, 255, 150), btn_restart, 2)
    screen.blit(font.render("Restart", True, (255, 255, 255)),
                (btn_restart.centerx - 45, btn_restart.centery - 15))

    # EXIT
    pygame.draw.rect(screen, (200, 80, 80), btn_exit)
    pygame.draw.rect(screen, (255, 150, 150), btn_exit, 2)
    screen.blit(font.render("Exit", True, (255, 255, 255)),
                (btn_exit.centerx - 25, btn_exit.centery - 15))

    return btn_prev, btn_next, btn_restart, btn_exit

def replay_step():
    global replay_index, replay_active

    if replay_index >= len(replay_moves):
        replay_active = False
        return

    move = replay_moves[replay_index]
    piece_color = WHITE if move["piece_color"] == "W" else BLACK

    # Convert algebraic notation to board coordinates
    token = move["move"]
    src = token[:2]
    dst = token[-2:]

    sr = 8 - int(src[1])
    sc = "abcdefgh".index(src[0])
    dr = 8 - int(dst[1])
    dc = "abcdefgh".index(dst[0])

    # Find piece at source
    piece = piece_at(sr, sc)
    if not piece:
        replay_index += 1
        return

    # Perform move
    if abs(dr - sr) == 2:  # jump
        jumped = piece_at((sr + dr)//2, (sc + dc)//2)
        if jumped:
            board_state.remove(jumped)

    piece.update_location(board_to_pixel(dr, dc))

    # promote
    if (piece.player == WHITE and dr == 0) or (piece.player == BLACK and dr == 7):
        piece.make_king()

    replay_index += 1

################################################
# LOGIN SCREEN (Merged A + B)
################################################

login_active = False
login_username = ""
login_password = ""
login_message = ""
login_input = None          # "user" or "pass"

current_user = None

# PvP two-login support
login_stage = 0             # 0 = idle, 1 = Player 1 login, 2 = Player 2 login
player1_user = None
player2_user = None


def draw_login_screen():
    screen.fill((30, 30, 30))

    title_font = pygame.font.SysFont(None, int(60 * UI_SCALE))
    field_font = pygame.font.SysFont(None, int(32 * UI_SCALE))
    small_font = pygame.font.SysFont(None, int(24 * UI_SCALE))

    if pending_mode == "pvp":
        if login_stage == 1:
            title_text = "Player 1 Login / Register"
        elif login_stage == 2:
            title_text = "Player 2 Login / Register"
        else:
            title_text = "Login / Register"
    else:
        title_text = "Login / Register"

    title = title_font.render(title_text, True, (255, 255, 255))

    screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))

    box_w = int(300 * UI_SCALE)
    box_h = int(40 * UI_SCALE)
    start_x = SCREEN_WIDTH//2 - box_w//2

    # Username
    user_rect = pygame.Rect(start_x, 150, box_w, box_h)
    pygame.draw.rect(screen, (200, 200, 200), user_rect, 2)
    screen.blit(field_font.render("Username:", True, (200, 200, 200)),
                (user_rect.x, user_rect.y - 30))
    screen.blit(field_font.render(login_username, True, (255, 255, 255)),
                (user_rect.x + 8, user_rect.y + 5))

    # Password
    pass_rect = pygame.Rect(start_x, 230, box_w, box_h)
    pygame.draw.rect(screen, (200, 200, 200), pass_rect, 2)
    screen.blit(field_font.render("Password:", True, (200, 200, 200)),
                (pass_rect.x, pass_rect.y - 30))
    hidden = "*" * len(login_password)
    screen.blit(field_font.render(hidden, True, (255, 255, 255)),
                (pass_rect.x + 8, pass_rect.y + 5))

    # Login button
    login_rect = pygame.Rect(start_x, 310, box_w, box_h)
    pygame.draw.rect(screen, (0, 140, 255), login_rect)
    screen.blit(field_font.render("Login", True, (255, 255, 255)),
                (login_rect.centerx - 40, login_rect.centery - 15))

    # Register button
    reg_rect = pygame.Rect(start_x, 370, box_w, box_h)
    pygame.draw.rect(screen, (0, 180, 120), reg_rect)
    screen.blit(field_font.render("Register", True, (255, 255, 255)),
                (reg_rect.centerx - 55, reg_rect.centery - 15))

    # Status message
    if login_message:
        msg = small_font.render(login_message, True, (255, 180, 180))
        screen.blit(msg, (SCREEN_WIDTH//2 - msg.get_width()//2, 430))

    return user_rect, pass_rect, login_rect, reg_rect

################################################
# START MENU
################################################

start_menu_active = True
menu_buttons = {}

def draw_start_menu():
    screen.fill((40, 40, 40))

    # Title font and menu font scale with UI_SCALE
    font_big = pygame.font.SysFont(None, int(72 * UI_SCALE))
    font_small = pygame.font.SysFont(None, int(40 * UI_SCALE))

    # ----- Title -----
    title_surf = font_big.render("Penguin Checkers", True, (255, 255, 255))
    screen.blit(
        title_surf,
        (SCREEN_WIDTH // 2 - title_surf.get_width() // 2,
         int(50 * UI_SCALE))
    )

    # ----- Button geometry -----
    btn_w = int(360 * UI_SCALE)
    btn_h = int(40 * UI_SCALE)
    spacing = int(8 * UI_SCALE)

    x = SCREEN_WIDTH // 2 - btn_w // 2
    first_y = int(200 * UI_SCALE)

    btn_pvp    = pygame.Rect(x, first_y + 0 * (btn_h + spacing), btn_w, btn_h)
    btn_easy   = pygame.Rect(x, first_y + 1 * (btn_h + spacing), btn_w, btn_h)
    btn_hard   = pygame.Rect(x, first_y + 2 * (btn_h + spacing), btn_w, btn_h)
    btn_replay = pygame.Rect(x, first_y + 3 * (btn_h + spacing), btn_w, btn_h)

    # ----- Button backgrounds -----
    pygame.draw.rect(screen, ( 80,  80, 200), btn_pvp)
    pygame.draw.rect(screen, ( 80, 200,  80), btn_easy)
    pygame.draw.rect(screen, (200,  80,  80), btn_hard)
    pygame.draw.rect(screen, (100, 100, 100), btn_replay)

    # ----- Text surfaces -----
    txt_pvp    = font_small.render("Human vs Human",      True, (255, 255, 255))
    txt_easy   = font_small.render("Human vs AI (Easy)",  True, (255, 255, 255))
    txt_hard   = font_small.render("Human vs AI (Hard)",  True, (255, 255, 255))
    txt_replay = font_small.render("View Replays",        True, (255, 255, 255))

    # Helper to center text in a rect
    def blit_center(text_surf, rect):
        screen.blit(
            text_surf,
            (rect.centerx - text_surf.get_width() // 2,
             rect.centery - text_surf.get_height() // 2)
        )

    blit_center(txt_pvp,    btn_pvp)
    blit_center(txt_easy,   btn_easy)
    blit_center(txt_hard,   btn_hard)
    blit_center(txt_replay, btn_replay)

    # Store for clicks
    menu_buttons["pvp"]    = btn_pvp
    menu_buttons["easy"]   = btn_easy
    menu_buttons["hard"]   = btn_hard
    menu_buttons["replay"] = btn_replay

################################################
# IN-GAME MENU (settings)
################################################

settings_menu_active = False

def draw_settings_menu():
    menu_w = int(400 * MENU_SCALE)
    menu_h = int(300 * MENU_SCALE)
    x = (SCREEN_WIDTH - menu_w)//2
    y = (SCREEN_HEIGHT - menu_h)//2

    pygame.draw.rect(screen, (220, 220, 220), (x, y, menu_w, menu_h))
    pygame.draw.rect(screen, (100, 100, 100), (x, y, menu_w, menu_h), 4)

    font = pygame.font.SysFont(None, int(40 * MENU_SCALE))

    title = font.render("Settings", True, (0, 0, 0))
    screen.blit(title, (x + menu_w//2 - title.get_width()//2, y + 20))

    # Close button
    btn_close = pygame.Rect(x + menu_w - int(45 * MENU_SCALE), y + 10,
                            int(35 * MENU_SCALE), int(35 * MENU_SCALE))
    pygame.draw.rect(screen, (200, 50, 50), btn_close)
    screen.blit(font.render("X", True, (255, 255, 255)),
                (btn_close.centerx - 10, btn_close.centery - 18))

    # AI difficulty: Easy
    btn_easy = pygame.Rect(x + 50, y + 100, 120, 50)
    pygame.draw.rect(screen, (100, 200, 100) if AI_DIFFICULTY == "EASY" else (60, 120, 60), btn_easy)
    screen.blit(font.render("Easy", True, (0, 0, 0)), (btn_easy.x + 10, btn_easy.y + 5))

    # AI difficulty: Hard
    btn_hard = pygame.Rect(x + 50, y + 180, 120, 50)
    pygame.draw.rect(screen, (200, 120, 120) if AI_DIFFICULTY == "HARD" else (120, 60, 60), btn_hard)
    screen.blit(font.render("Hard", True, (0, 0, 0)), (btn_hard.x + 10, btn_hard.y + 5))

    # store for click detection
    menu_buttons["settings_close"] = btn_close
    menu_buttons["settings_easy"] = btn_easy
    menu_buttons["settings_hard"] = btn_hard


################################################
# TOP UI BUTTONS (Menu / Reset / Replay)
################################################

################################################
# TOP UI BAR + BUTTONS
################################################

def draw_ui_buttons():
    # Draw the gray UI bar across the top
    pygame.draw.rect(screen, (50, 50, 50), (0, 0, SCREEN_WIDTH, UI_SPACE_HEIGHT))
    pygame.draw.rect(screen, (100, 100, 100), (0, 0, SCREEN_WIDTH, UI_SPACE_HEIGHT), 4)

    font_size = int(36 * UI_SCALE)
    ui_font = pygame.font.SysFont(None, font_size)

    # Turn indicator text on the left
    turn_text = ui_font.render(f"Turn: {'White' if turn % 2 == 0 else 'Black'}",
                               True, (255, 255, 255))
    screen.blit(turn_text, (10 * UI_SCALE, 10 * UI_SCALE))

    # Buttons on the right side of the bar
    button_w = int(100 * UI_SCALE)
    button_h = int(40 * UI_SCALE)
    padding = int(10 * UI_SCALE)

    # Layout: [Menu] [Reset] [Replay] from right to left
    replay_button = pygame.Rect(
        SCREEN_WIDTH - (button_w + padding),
        padding,
        button_w,
        button_h
    )

    reset_button = pygame.Rect(
        SCREEN_WIDTH - (button_w * 2 + padding * 2),
        padding,
        button_w,
        button_h
    )

    menu_button = pygame.Rect(
        SCREEN_WIDTH - (button_w * 3 + padding * 3),
        padding,
        button_w,
        button_h
    )

    # Menu button visuals
    pygame.draw.rect(screen, (50, 50, 150), menu_button)
    pygame.draw.rect(screen, (100, 100, 200), menu_button, 2)
    menu_text = ui_font.render("Menu", True, (255, 255, 255))
    screen.blit(menu_text,
                (menu_button.centerx - menu_text.get_width() // 2,
                 menu_button.centery - menu_text.get_height() // 2))

    # Reset button visuals
    pygame.draw.rect(screen, (150, 50, 50), reset_button)
    pygame.draw.rect(screen, (200, 100, 100), reset_button, 2)
    reset_text = ui_font.render("Reset", True, (255, 255, 255))
    screen.blit(reset_text,
                (reset_button.centerx - reset_text.get_width() // 2,
                 reset_button.centery - reset_text.get_height() // 2))

    # Replay button visuals
    pygame.draw.rect(screen, (50, 150, 50), replay_button)
    pygame.draw.rect(screen, (100, 200, 100), replay_button, 2)
    replay_text = ui_font.render("Replay", True, (255, 255, 255))
    screen.blit(replay_text,
                (replay_button.centerx - replay_text.get_width() // 2,
                 replay_button.centery - replay_text.get_height() // 2))

    return menu_button, reset_button, replay_button


################################################
# SCALING
################################################
def draw_board():
    for row in range(ROWS):
        for col in range(ROWS):
            x = BOARD_OFFSET_X + col * TILE_SIZE
            y = UI_SPACE_HEIGHT + row * TILE_SIZE
            color = WHITE_TILE if (row + col) % 2 == 0 else BLUE_TILE
            pygame.draw.rect(screen, color, (x, y, TILE_SIZE, TILE_SIZE))


def draw_all_pieces():
    for p in board_state:
        p.draw_self()

def scale_window(new_size):
    global SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, BOARD_SIZE, BOARD_OFFSET_X
    global UI_SPACE_HEIGHT, screen, UI_SCALE, MENU_SCALE

    old_tile = TILE_SIZE
    old_offset_x = BOARD_OFFSET_X
    old_ui = UI_SPACE_HEIGHT

    SCREEN_WIDTH, SCREEN_HEIGHT = new_size
    SCREEN_HEIGHT = max(SCREEN_HEIGHT, 500)

    UI_SCALE = SCREEN_WIDTH / 800
    MENU_SCALE = UI_SCALE
    UI_SPACE_HEIGHT = max(40, int(60 * UI_SCALE))

    side = min(SCREEN_WIDTH, SCREEN_HEIGHT - UI_SPACE_HEIGHT)
    TILE_SIZE = side // 8
    BOARD_SIZE = TILE_SIZE * 8
    BOARD_OFFSET_X = (SCREEN_WIDTH - BOARD_SIZE)//2

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)

    rescale_penguin_images()

    # reposition pieces
    for p in board_state:
        x, y = p.location
        old_col = int((x - old_offset_x) // old_tile)
        old_row = int((y - old_ui) // old_tile)
        if 0 <= old_row < 8 and 0 <= old_col < 8:
            new_x = BOARD_OFFSET_X + old_col * TILE_SIZE + TILE_SIZE//2
            new_y = UI_SPACE_HEIGHT + old_row * TILE_SIZE + TILE_SIZE//2
            p.location = (new_x, new_y)
            p.radius = TILE_SIZE//3
            p.update_rect()

    pygame.display.flip()


################################################
# REPLAY FILE LIST SCREEN
################################################

def draw_replay_file_list():
    screen.fill((20, 20, 20))
    font_big = pygame.font.SysFont(None, int(60 * UI_SCALE))
    font_small = pygame.font.SysFont(None, int(32 * UI_SCALE))

    title = font_big.render("Replay Files", True, (255, 255, 255))
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 40))

    # Exit / Back button (top-right)
    exit_w = int(150 * UI_SCALE)
    exit_h = int(50 * UI_SCALE)
    exit_x = SCREEN_WIDTH - exit_w - 20
    exit_y = 20

    exit_rect = pygame.Rect(exit_x, exit_y, exit_w, exit_h)
    pygame.draw.rect(screen, (180, 50, 50), exit_rect)
    pygame.draw.rect(screen, (250, 120, 120), exit_rect, 2)

    exit_text = font_small.render("Back", True, (255, 255, 255))
    screen.blit(
        exit_text,
        (exit_rect.centerx - exit_text.get_width() // 2,
         exit_rect.centery - exit_text.get_height() // 2)
    )

    # List of replay entries
    files = load_replay_list()
    buttons = []
    y = 150

    for idx, game in enumerate(files):
        rect = pygame.Rect(100, y, SCREEN_WIDTH - 200, int(60 * UI_SCALE))
        pygame.draw.rect(screen, (80, 80, 80), rect)
        pygame.draw.rect(screen, (150, 150, 150), rect, 2)


        players = game.get("players", {})
        white_name = players.get("white") or game.get("white_player", "?")
        black_name = players.get("black") or game.get("black_player", "?")
        winner = game.get("winner", "?")

        label = f"{idx + 1}: {white_name} vs {black_name} (winner: {winner})"

        screen.blit(font_small.render(label, True, (255, 255, 255)),
                    (rect.x + 10, rect.y + 15))

        buttons.append((rect, idx))
        y += int(80 * UI_SCALE)

    # Return both the file buttons and the exit button rect
    return buttons, exit_rect

def draw_replay_exit_button():
    font = pygame.font.SysFont(None, int(32 * UI_SCALE))
    w = int(150 * UI_SCALE)
    h = int(50 * UI_SCALE)
    x = SCREEN_WIDTH - w - 20
    y = 20

    rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, (180, 50, 50), rect)
    pygame.draw.rect(screen, (250, 120, 120), rect, 2)

    text = font.render("Exit Replay", True, (255, 255, 255))
    screen.blit(text, (rect.centerx - text.get_width()//2,
                       rect.centery - text.get_height()//2))
    return rect


running = True
if __name__ == "__main__":
    while running:
        clock.tick(60)
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.VIDEORESIZE:
                scale_window(event.size)

            # ---------- START MENU FIRST ----------
            if start_menu_active:
                draw_start_menu()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if menu_buttons["pvp"].collidepoint(event.pos):
                        pending_mode = "pvp"
                        login_active = True
                        start_menu_active = False
                        login_message = ""
                        login_username = ""
                        login_password = ""
                        login_stage = 1  # start with Player 1
                        player1_user = None
                        player2_user = None

                    elif menu_buttons["easy"].collidepoint(event.pos):
                        pending_mode = "ai_easy"
                        login_active = True
                        start_menu_active = False
                        login_message = ""
                        login_username = ""
                        login_password = ""
                        login_stage = 1  # just one login (human)
                        player1_user = None
                        player2_user = "AI"

                    elif menu_buttons["hard"].collidepoint(event.pos):
                        pending_mode = "ai_hard"
                        login_active = True
                        start_menu_active = False
                        login_message = ""
                        login_username = ""
                        login_password = ""
                        login_stage = 1  # just one login (human)
                        player1_user = None
                        player2_user = "AI"

                    elif menu_buttons["replay"].collidepoint(event.pos):
                        start_menu_active = False
                        replay_select_active = True

                continue  # skip rest while on start menu

            # ---------- LOGIN AFTER MODE ----------
            if login_active:
                user_rect, pass_rect, login_rect, reg_rect = draw_login_screen()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if user_rect.collidepoint(event.pos):
                        login_input = "user"
                    elif pass_rect.collidepoint(event.pos):
                        login_input = "pass"

                    elif login_rect.collidepoint(event.pos):
                        # LOGIN existing user
                        ok, msg = verify_login(login_username, login_password)
                        login_message = msg
                        if ok:
                            if pending_mode == "pvp":
                                # two-player login
                                if login_stage == 1:
                                    player1_user = login_username
                                    login_message = "Player 1 logged in. Now Player 2."
                                    login_username = ""
                                    login_password = ""
                                    login_stage = 2
                                elif login_stage == 2:
                                    player2_user = login_username
                                    current_user = player1_user  # "main" user if you need one
                                    login_active = False
                                    login_stage = 0
                                    game_vs_ai = False
                                    reset_game()
                            else:
                                # single-player vs AI
                                player1_user = login_username
                                player2_user = "AI"
                                current_user = login_username
                                login_active = False
                                login_stage = 0

                                game_vs_ai = True
                                if pending_mode == "ai_easy":
                                    AI_DIFFICULTY = "EASY"
                                elif pending_mode == "ai_hard":
                                    AI_DIFFICULTY = "HARD"

                                reset_game()

                    elif reg_rect.collidepoint(event.pos):
                        # REGISTER new user
                        ok, msg = register_user(login_username, login_password)
                        login_message = msg
                        if ok:
                            if pending_mode == "pvp":
                                if login_stage == 1:
                                    player1_user = login_username
                                    login_message = "Player 1 registered. Now Player 2."
                                    login_username = ""
                                    login_password = ""
                                    login_stage = 2
                                elif login_stage == 2:
                                    player2_user = login_username
                                    current_user = player1_user
                                    login_active = False
                                    login_stage = 0
                                    game_vs_ai = False
                                    reset_game()
                            else:
                                # single-player vs AI
                                player1_user = login_username
                                player2_user = "AI"
                                current_user = login_username
                                login_active = False
                                login_stage = 0

                                game_vs_ai = True
                                if pending_mode == "ai_easy":
                                    AI_DIFFICULTY = "EASY"
                                elif pending_mode == "ai_hard":
                                    AI_DIFFICULTY = "HARD"

                                reset_game()

                    elif reg_rect.collidepoint(event.pos):
                        # REGISTER
                        ok, msg = register_user(login_username, login_password)
                        login_message = msg
                        if ok:
                            # auto-login after registration
                            current_user = login_username
                            login_active = False

                            if pending_mode == "pvp":
                                game_vs_ai = False
                            elif pending_mode == "ai_easy":
                                game_vs_ai = True
                                AI_DIFFICULTY = "EASY"
                            elif pending_mode == "ai_hard":
                                game_vs_ai = True
                                AI_DIFFICULTY = "HARD"

                            reset_game()

                if event.type == pygame.KEYDOWN:
                    if login_input == "user":
                        if event.key == pygame.K_BACKSPACE:
                            login_username = login_username[:-1]
                        else:
                            login_username += event.unicode
                    elif login_input == "pass":
                        if event.key == pygame.K_BACKSPACE:
                            login_password = login_password[:-1]
                        else:
                            login_password += event.unicode

                continue  # skip rest while on login screen

            ########################################
            # REPLAY FILE SELECT MENU
            ########################################
            if replay_select_active:
                buttons, exit_rect = draw_replay_file_list()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Clicked a replay file
                    for rect, idx in buttons:
                        if rect.collidepoint(event.pos):
                            game_data = load_replay_game(idx)
                            if game_data is not None:
                                start_replay(game_data)
                                replay_select_active = False
                            break

                    # Clicked the Back/Exit button
                    if exit_rect.collidepoint(event.pos):
                        replay_select_active = False

                        start_menu_active = True

                continue

            ########################################
            # REPLAY MODE ACTIVE
            ########################################

            ########################################
            # REPLAY MODE ACTIVE (manual controls)
            ########################################
            if replay_active:
                # Only handle clicks here, NO drawing / flip
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Recreate the same rects as in draw_replay_controls()
                    btn_h = int(45 * UI_SCALE)
                    btn_w = int(140 * UI_SCALE)
                    pad = int(15 * UI_SCALE)
                    top_y = pad

                    btn_prev = pygame.Rect(pad, top_y, btn_w, btn_h)
                    btn_next = pygame.Rect(pad + btn_w + pad, top_y, btn_w, btn_h)
                    btn_restart = pygame.Rect(pad + (btn_w + pad) * 2, top_y, btn_w, btn_h)
                    btn_exit = pygame.Rect(pad + (btn_w + pad) * 3, top_y, btn_w, btn_h)

                    # Back one move
                    if btn_prev.collidepoint(event.pos):
                        if replay_index > 0:
                            replay_index -= 1
                            reset_board_for_replay()

                    # Forward one move
                    elif btn_next.collidepoint(event.pos):
                        if replay_index < len(replay_moves):
                            apply_replay_move_index(replay_index)
                            replay_index += 1

                    # Restart
                    elif btn_restart.collidepoint(event.pos):
                        replay_index = 0
                        reset_board_for_replay()

                    # Exit replay
                    elif btn_exit.collidepoint(event.pos):
                        replay_active = False
                        replay_index = 0
                        start_menu_active = True


                continue

            ########################################
            # SETTINGS MENU
            ########################################
            if settings_menu_active:
                draw_settings_menu()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if menu_buttons["settings_close"].collidepoint(event.pos):
                        settings_menu_active = False
                    elif menu_buttons["settings_easy"].collidepoint(event.pos):
                        AI_DIFFICULTY = "EASY"
                    elif menu_buttons["settings_hard"].collidepoint(event.pos):
                        AI_DIFFICULTY = "HARD"

                pygame.display.flip()
                continue

            ########################################
            # NORMAL GAMEPLAY
            ########################################

            btn_menu, btn_reset, btn_replay = draw_ui_buttons()

            # Top buttons
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_menu.collidepoint(event.pos):
                    settings_menu_active = True
                    continue
                if btn_reset.collidepoint(event.pos):
                    reset_game()
                    continue
                if btn_replay.collidepoint(event.pos):
                    replay_select_active = True
                    continue

            # No moves if game over
            if game_over:
                continue

            ########################################
            # PLAYER CLICK PIECE (select)
            ########################################
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not dragging:
                    for p in board_state:
                        if p.clicked(event.pos) and p.player == get_current_turn():
                            forced = get_forced_jump_pieces(get_current_turn())
                            if forced and p not in forced:
                                break

                            valid = get_valid_moves(p, only_jumps=bool(forced))
                            if valid:
                                selected_piece = p
                                valid_moves = valid
                                dragging = True
                                drag_origin = p.location
                                break

            ########################################
            # DRAGGING A PIECE
            ########################################
            if event.type == pygame.MOUSEMOTION and dragging and selected_piece:
                selected_piece.update_location(event.pos)

            ########################################
            # RELEASE PIECE (drop)
            ########################################
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and dragging:
                dragging = False

                if not selected_piece:
                    continue

                sr, sc = pixel_to_board(drag_origin)
                dr, dc = pixel_to_board(event.pos)

                if (dr, dc) not in valid_moves:
                    selected_piece.update_location(drag_origin)
                    selected_piece = None
                    valid_moves = []
                    continue

                result = execute_move(selected_piece, sr, sc, dr, dc)



                selected_piece = None
                valid_moves = []

                # ---- AI RESPONSE TURN ----
                if game_vs_ai and not game_over and get_current_turn() == AI_COLOR:
                    if AI_DIFFICULTY == "EASY":
                        ai = easy_AI(AI_COLOR)
                    else:
                        ai = hard_AI(AI_COLOR)
                    apply_ai_move(ai)

        ###############################################
        # DRAW FRAME
        ###############################################
        screen.fill((0, 0, 0))

        if login_active:
            draw_login_screen()
        elif start_menu_active:
            draw_start_menu()
        elif replay_select_active:
            draw_replay_file_list()
        elif replay_active:
            draw_board()
            draw_all_pieces()
            draw_replay_controls()

        else:
            draw_board()
            draw_all_pieces()
            draw_ui_buttons()

            # highlight valid moves
            if selected_piece:
                for r, c in valid_moves:
                    pygame.draw.circle(screen, (255, 255, 0),
                                       board_to_pixel(r, c), TILE_SIZE//6)

            # highlight forced pieces
            for p in get_forced_jump_pieces(get_current_turn()):
                pygame.draw.circle(screen, (255, 255, 0),
                                   p.location, p.radius + 5, 3)

            # highlight selected
            if selected_piece:
                pygame.draw.circle(screen, (255, 0, 0),
                                   selected_piece.location, selected_piece.radius + 5, 3)

            # show settings menu on top
            if settings_menu_active:
                draw_settings_menu()

            # game over
            if game_over:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                overlay.set_alpha(180)
                overlay.fill((0, 0, 0))
                screen.blit(overlay, (0, 0))

                end_font = pygame.font.SysFont(None, int(60 * UI_SCALE))
                text = end_font.render(f"Game Over — {game_winner} Wins!", True, (255, 255, 255))
                screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2,
                                   SCREEN_HEIGHT//2 - text.get_height()//2))

        pygame.display.flip()

    pygame.quit()
