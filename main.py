import pygame
import time
import random
import json
import hashlib
import os
import datetime

# Initialize Pygame
pygame.init()

# -----------------------------
# Window / Board Setup
# -----------------------------
# create an 800x800 window initially with scalability
UI_SPACE_HEIGHT = 60
info = pygame.display.Info()
SCREEN_WIDTH = min(info.current_w - 100, 800)
SCREEN_HEIGHT = min(info.current_h - 100, 800) + 60
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT),
                                 pygame.RESIZABLE)  # add pygame.RESIZABLE if you want to mess with scaling (I do not right now)
pygame.display.set_caption("Penguin Checkers")
menu_buttons = {
    "close": None,
    "easy": None,
    "hard": None
}

# Options for AI difficulty
AI_DIFFICULTY = "EASY"  # "EASY" or "HARD"

UI_SCALE = 1.0
MENU_SCALE = 1.0

# calc tile size based on screen
TILE_SIZE = min(SCREEN_WIDTH, SCREEN_HEIGHT) // 8
BOARD_SIZE = TILE_SIZE * 8
BOARD_OFFSET_X = (SCREEN_WIDTH - BOARD_SIZE) // 2
BOARD_OFFSET_Y = 0
ROWS = 8

# Define board colors (light and dark squares)
BLUE_TILE = (0, 102, 204)  # Dark squares (blue)
WHITE_TILE = (255, 255, 255)  # Light squares (white)

# Define piece colors
BLACK = (35, 35, 35)  # Black player pieces
BLACK_BORDER = (70, 70, 70)
WHITE = (255, 255, 255)  # White player pieces
WHITE_BORDER = (200, 200, 200)
HIGHLIGHT_WIDTH = 5

# Define colors for highlights and effects
HIGHLIGHT_YELLOW = (255, 255, 0)  # Used for showing valid move options
HIGHLIGHT_GREEN = (0, 255, 0)  # Used for hovering
HIGHLIGHT_RED = (255, 0, 0)  # Used for selected pieces
HIGHLIGHT_GOLD = (255, 215, 0)  # Used for kings (gold center)

# Clock object to control how fast the game updates (60 FPS)
clock = pygame.time.Clock()

# -----------------------------
# Penguin sprite integration
# -----------------------------
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
except Exception as e:
    # If images are missing or fail to load, fall back to circle rendering.
    BLACK_PENGUIN_BASE = None
    WHITE_PENGUIN_BASE = None
    BLACK_PENGUIN_KING_BASE = None
    WHITE_PENGUIN_KING_BASE = None


def rescale_penguin_images():
    """Resize penguin images to match TILE_SIZE (called at startup and on resize)."""
    global BLACK_PENGUIN, WHITE_PENGUIN, BLACK_PENGUIN_KING, WHITE_PENGUIN_KING
    size = max(1, int(TILE_SIZE * 0.9))  # ensure non-zero size
    if BLACK_PENGUIN_BASE and WHITE_PENGUIN_BASE and BLACK_PENGUIN_KING_BASE and WHITE_PENGUIN_KING_BASE:
        BLACK_PENGUIN = pygame.transform.smoothscale(BLACK_PENGUIN_BASE, (size, size))
        WHITE_PENGUIN = pygame.transform.smoothscale(WHITE_PENGUIN_BASE, (size, size))
        BLACK_PENGUIN_KING = pygame.transform.smoothscale(BLACK_PENGUIN_KING_BASE, (size, size))
        WHITE_PENGUIN_KING = pygame.transform.smoothscale(WHITE_PENGUIN_KING_BASE, (size, size))
    else:
        BLACK_PENGUIN = WHITE_PENGUIN = BLACK_PENGUIN_KING = WHITE_PENGUIN_KING = None


# initial rescale
rescale_penguin_images()

# -----------------------------
# Game state variables
# -----------------------------
# store game state and history
board_state = []
board_history = []

# Variables used for selecting and moving pieces
# even = white's turn, odd = black's turn
turn = 0
selected_piece = None
valid_moves = []
dragging = False
orig_pos = None
offset_x = offset_y = 0
multi_jump = False
jump_occurred = False
game_over = False
game_winner = None
show_menu = False
hover_piece = None

# Login system state
login_screen_active = True
register_mode = False
login_username = ""
login_password = ""
login_message = ""
input_active = None  # "username" or "password"
# Two-player login system
login_screen_active = False  # start inactive
login_stage = "P1"           # reset just before login
mode_select_active = True     # start at mode selection


# Game mode system
game_mode = None  # "PVP", "AI_EASY", "AI_HARD"
mode_select_active = True

# Game record directory
if not os.path.exists("games"):
    os.makedirs("games")

# Tracks the algebraic move history of the current game
move_history = []

# -----------------------------
# REPLAY SYSTEM STATE
# -----------------------------
replay_mode_active = False
replay_file_select_active = False
replay_moves = []
replay_index = 0
replay_total = 0
replay_record = None


# -----------------------------
# Checker Class - represents one checker piece
# -----------------------------
class Checker:
    def __init__(self, location, status, player):
        self.location = location  # Current pixel position of the piece (center)
        self.status = status  # "normal" or "king"
        self.player = player  # Which player this piece belongs to (WHITE/BLACK)
        self.king = False  # Whether the piece is a king yet
        # radius retained for some highlight calculations (not used for sprite size)
        self.radius = TILE_SIZE // 3
        # White pieces move up (-1), Black pieces move down (+1)
        self.direction = -1 if player == WHITE else 1
        self.update_rect()  # Define the clickable area

    def update_location(self, new_location):
        """Move the piece to a new pixel location and check for king promotion."""
        self.location = new_location
        self.update_rect()

        # Promote to king when reaching the far end of the board
        r, _ = pixel_to_board(new_location)
        if not self.king:
            if self.player == WHITE and r == 0:
                self.make_king()
            elif self.player == BLACK and r == ROWS - 1:
                self.make_king()

    def update_rect(self):
        """Define the rectangular area around the piece for click detection."""
        # Use the sprite size if available, otherwise fall back to radius-based rect
        if BLACK_PENGUIN is not None:
            img_w = BLACK_PENGUIN.get_width()
            img_h = BLACK_PENGUIN.get_height()
            self.rect = pygame.Rect(0, 0, img_w, img_h)
            self.rect.center = self.location
        else:
            self.rect = pygame.Rect(
                self.location[0] - self.radius,
                self.location[1] - self.radius,
                self.radius * 2,
                self.radius * 2
            )

    def make_king(self):
        """Turn this piece into a king."""
        self.king = True
        self.direction = 0  # Kings can move both directions
        self.status = "king"

    def draw_self(self):
        """Draw the piece on the board using penguin sprites if available."""
        if BLACK_PENGUIN is None:
            # fallback to original circle drawing
            pygame.draw.circle(screen, self.player, self.location, self.radius)
            if self.player == WHITE:
                pygame.draw.circle(screen, WHITE_BORDER, self.location, self.radius, HIGHLIGHT_WIDTH)
            else:
                pygame.draw.circle(screen, BLACK_BORDER, self.location, self.radius, HIGHLIGHT_WIDTH)
            if self.king:
                pygame.draw.circle(screen, HIGHLIGHT_GOLD, self.location, self.radius // 2)
            return

        # choose correct image depending on player and king status
        if self.player == WHITE:
            img = WHITE_PENGUIN_KING if self.king else WHITE_PENGUIN
        else:
            img = BLACK_PENGUIN_KING if self.king else BLACK_PENGUIN

        if img:
            rect = img.get_rect(center=self.location)
            screen.blit(img, rect)
        else:
            # Extremely defensive fallback
            pygame.draw.circle(screen, self.player, self.location, self.radius)
            if self.king:
                pygame.draw.circle(screen, HIGHLIGHT_GOLD, self.location, self.radius // 2)

    def clicked(self, mouse_pos):
        """Return True if the mouse clicked on this piece."""
        return self.rect.collidepoint(mouse_pos)


class easy_AI:
    def __init__(self, color):
        self.color = color

    def pick_move(self):
        moves = get_all_player_moves(self.color)

        if not moves:
            return None

        piece, (r, c) = random.choice(moves)
        return piece, (r, c)


class hard_AI:
    def __init__(self, color):
        self.color = color

    def pick_move(self):
        moves = get_all_player_moves(self.color)
        if not moves:
            return None

        scored_moves = []
        for piece, (r, c) in moves:
            score = self.evaluate_move(piece, r, c)
            scored_moves.append((score, piece, (r, c)))

        scored_moves.sort(reverse=True, key=lambda x: x[0])
        _, piece, move = scored_moves[0]
        return piece, move

    def evaluate_move(self, piece, r, c):
        sr, sc = pixel_to_board(piece.location)
        dr = r - sr
        score = 0

        # Prefer advancing pieces toward promotion
        if piece.player == BLACK:
            score += dr
        else:
            score -= dr

        # Promote to king
        if piece.player == BLACK and r == ROWS - 1:
            score += 10
        elif piece.player == WHITE and r == 0:
            score += 10

        # Prefer jumps (captures)
        if abs(dr) == 2:
            score += 5

        # Prefer center squares
        if 2 <= r <= 5 and 2 <= c <= 5:
            score += 1

        # Small random factor for unpredictability
        score += random.uniform(0, 0.5)

        return score


# -----------------------------
# Algebraic Notation Helpers
# -----------------------------
def to_algebraic(row, col):
    # Columns a–h, rows 1–8
    return chr(ord('a') + col) + str(8 - row)


def algebraic_move(start_r, start_c, end_r, end_c, is_jump):
    start = to_algebraic(start_r, start_c)
    end = to_algebraic(end_r, end_c)
    return f"{start}x{end}" if is_jump else f"{start}-{end}"


# -----------------------------
# Helper Functions
# -----------------------------
def get_current_turn():
    return WHITE if turn % 2 == 0 else BLACK


def pixel_to_board(pos):
    x, y = pos
    board_x = x - BOARD_OFFSET_X
    board_y = y - UI_SPACE_HEIGHT

    if 0 <= board_x < BOARD_SIZE and 0 <= board_y < BOARD_SIZE:
        col = int(board_x // TILE_SIZE)
        row = int(board_y // TILE_SIZE)
        return row, col
    return -1, -1


def draw_ai_difficulty():
    ui_font = pygame.font.SysFont(None, int(24 * UI_SCALE))
    text = ui_font.render(f"AI Difficulty: {AI_DIFFICULTY}", True, (255, 255, 255))
    screen.blit(text, (SCREEN_WIDTH - 250, 10 * UI_SCALE))


def board_to_pixel(row, col):
    x = BOARD_OFFSET_X + col * TILE_SIZE + TILE_SIZE // 2
    y = UI_SPACE_HEIGHT + row * TILE_SIZE + TILE_SIZE // 2
    return (x, y)


def board_to_screen_pixel(row, col):
    # need this for all the graphics elements to work
    x = BOARD_OFFSET_X + col * TILE_SIZE + TILE_SIZE // 2
    y = UI_SPACE_HEIGHT + row * TILE_SIZE + TILE_SIZE // 2
    return (x, y)


def is_dark_square(r, c):
    return (r + c) % 2 != 0


def piece_at(row, col):
    """Check if a piece exists at a specific board position."""
    for p in board_state:
        pr, pc = pixel_to_board(p.location)
        if pr == row and pc == col:
            return p
    return None


def create_starting_pieces():
    board_state.clear()

    for r in range(ROWS):
        for c in range(ROWS):
            # Pieces only sit on dark squares
            if not is_dark_square(r, c):
                continue

            x, y = board_to_pixel(r, c)

            # Black pieces occupy the top 3 rows
            if r < 3:
                board_state.append(Checker((x, y), "normal", BLACK))
            # White pieces occupy the bottom 3 rows
            elif r > 4:
                board_state.append(Checker((x, y), "normal", WHITE))


def draw_mode_select():
    screen.fill((40, 40, 40))
    font_big = pygame.font.SysFont(None, 60)
    font_small = pygame.font.SysFont(None, 36)

    title = font_big.render("Select Game Mode", True, (255, 255, 255))
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 60))

    btn_w, btn_h = 300, 60
    x = SCREEN_WIDTH // 2 - btn_w // 2

    btn1 = pygame.Rect(x, 180, btn_w, btn_h)
    btn2 = pygame.Rect(x, 260, btn_w, btn_h)
    btn3 = pygame.Rect(x, 340, btn_w, btn_h)

    pygame.draw.rect(screen, (80, 80, 200), btn1)
    pygame.draw.rect(screen, (80, 200, 80), btn2)
    pygame.draw.rect(screen, (200, 80, 80), btn3)

    screen.blit(font_small.render("Human vs Human", True, (255, 255, 255)),
                (btn1.centerx - 120, btn1.centery - 15))

    screen.blit(font_small.render("Human vs AI (Easy)", True, (255, 255, 255)),
                (btn2.centerx - 130, btn2.centery - 15))

    screen.blit(font_small.render("Human vs AI (Hard)", True, (255, 255, 255)),
                (btn3.centerx - 130, btn3.centery - 15))

    return btn1, btn2, btn3


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


def get_valid_moves(piece, only_jumps=False):
    """Find valid diagonal moves (and jumps) for a piece."""
    moves = []
    r, c = pixel_to_board(piece.location)

    # King can move all four directions; normal pieces move forward only
    if piece.king:
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    else:
        directions = [(piece.direction, -1), (piece.direction, 1)]

    jumps = []

    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        # Ensure the next square is on the board and dark
        if 0 <= nr < ROWS and 0 <= nc < ROWS and is_dark_square(nr, nc):
            target = piece_at(nr, nc)
            # Normal move (if square is empty and no jumps are required)
            if not target and not only_jumps:
                moves.append((nr, nc))
            # Check if a jump move is possible (skipping over an opponent)
            jr, jc = r + dr * 2, c + dc * 2
            if 0 <= jr < ROWS and 0 <= jc < ROWS and is_dark_square(jr, jc):
                jumped = piece_at(nr, nc)
                if jumped and jumped.player != piece.player and not piece_at(jr, jc):
                    jumps.append((jr, jc))
    # If any jumps exist, they take priority
    return jumps if jumps else moves


def get_forced_jump_pieces(player_color):
    pieces = [p for p in board_state if p.player == player_color]
    jump_pieces = []
    for piece in pieces:
        # Check if this piece has any jump moves available
        jump_moves = get_valid_moves(piece, only_jumps=True)
        if jump_moves:  # If there are any jump moves, this piece must jump
            jump_pieces.append(piece)
    return jump_pieces


def reset_game():
    save_game_record()
    global board_state, turn, selected_piece, valid_moves, dragging
    global orig_pos, multi_jump, jump_occurred, hover_piece, game_over, game_winner, board_history
    create_starting_pieces()
    # even = white turn, odd = black turn
    turn = 0
    selected_piece = None
    valid_moves = []
    dragging = False
    orig_pos = None
    multi_jump = False
    jump_occurred = False
    hover_piece = None
    game_over = False
    game_winner = None
    board_history = []
    global move_history
    move_history = []



def check_game_over():
    global game_over, game_winner

    # get num pieces for each player
    white_pieces = [p for p in board_state if p.player == WHITE]
    black_pieces = [p for p in board_state if p.player == BLACK]

    if len(white_pieces) == 0:
        game_over = True
        game_winner = "BLACK"

        return True
    if len(black_pieces) == 0:
        game_over = True
        game_winner = "WHITE"
        save_game_record()

        return True

    current_player_pieces = [p for p in board_state if p.player == get_current_turn()]
    has_valid_move = False

    for piece in current_player_pieces:
        if get_valid_moves(piece):
            has_valid_move = True
            break

    if not has_valid_move:
        # current player has no valid moves, game over
        game_over = True
        game_winner = "BLACK" if get_current_turn() == WHITE else "WHITE"
        return True
    return False


def draw_login_screen():
    screen.fill((30, 30, 30))

    font_big = pygame.font.SysFont(None, 60)
    font_small = pygame.font.SysFont(None, 36)

    player_title = "Player 1 Login" if login_stage == "P1" else "Player 2 Login"
    title = player_title if not register_mode else "Register New Account"

    title_surface = font_big.render(title, True, (255, 255, 255))
    screen.blit(title_surface, (SCREEN_WIDTH // 2 - title_surface.get_width() // 2, 50))

    # Input boxes
    box_w, box_h = 300, 40
    x = SCREEN_WIDTH // 2 - box_w // 2
    y_user = 150
    y_pass = 220

    # USERNAME BOX
    pygame.draw.rect(screen, (200, 200, 200), (x, y_user, box_w, box_h), 2)
    screen.blit(font_small.render(login_username, True, (255, 255, 255)), (x + 10, y_user + 5))

    # PASSWORD BOX (hide text)
    pygame.draw.rect(screen, (200, 200, 200), (x, y_pass, box_w, box_h), 2)
    hidden = "*" * len(login_password)
    screen.blit(font_small.render(hidden, True, (255, 255, 255)), (x + 10, y_pass + 5))

    # SUBMIT BUTTON
    btn = pygame.Rect(x, 300, box_w, box_h)
    pygame.draw.rect(screen, (0, 120, 255), btn)
    screen.blit(font_small.render("Submit", True, (255, 255, 255)),
                (btn.centerx - 50, btn.centery - 15))

    # Switch mode link
    switch_text = "Need an account? Register" if not register_mode else "Have an account? Login"
    screen.blit(font_small.render(switch_text, True, (200, 200, 100)),
                (x, 360))

    # Message output
    if login_message:
        msg = font_small.render(login_message, True, (255, 150, 150))
        screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, 420))

    return btn, pygame.Rect(x, y_user, box_w, box_h), pygame.Rect(x, y_pass, box_w, box_h), pygame.Rect(x, 360, 300, 40)


def draw_replay_file_select():
    screen.fill((30, 30, 30))
    font_big = pygame.font.SysFont(None, 60)
    font_small = pygame.font.SysFont(None, 36)

    title = font_big.render("Select Replay File", True, (255, 255, 255))
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 40))

    files = os.listdir("games")
    json_files = [f for f in files if f.endswith(".json")]

    buttons = []

    y = 150
    for f in json_files:
        rect = pygame.Rect(100, y, SCREEN_WIDTH - 200, 50)
        pygame.draw.rect(screen, (80, 80, 80), rect)
        pygame.draw.rect(screen, (160, 160, 160), rect, 2)

        screen.blit(font_small.render(f, True, (255, 255, 255)),
                    (rect.x + 10, rect.y + 10))
        buttons.append((rect, f))
        y += 70

    return buttons


def load_replay_file(filename):
    global replay_moves, replay_index, replay_total, replay_record

    with open("games/" + filename, "r") as f:
        replay_record = json.load(f)

    replay_moves = replay_record["moves"]
    replay_index = 0
    replay_total = len(replay_moves)


def apply_replay_move(move):
    # ex: "c3-d4" or "e5xf4"
    is_jump = "x" in move
    parts = move.replace("x", "-").split("-")

    start = parts[0]
    end = parts[1]

    start_col = ord(start[0]) - ord('a')
    start_row = 8 - int(start[1])

    end_col = ord(end[0]) - ord('a')
    end_row = 8 - int(end[1])

    piece = piece_at(start_row, start_col)
    if not piece:
        return

    # handle capture
    if is_jump:
        mid_r = (start_row + end_row) // 2
        mid_c = (start_col + end_col) // 2
        jumped_piece = piece_at(mid_r, mid_c)
        if jumped_piece:
            board_state.remove(jumped_piece)

    # move piece
    piece.update_location(board_to_pixel(end_row, end_col))


def reset_board_for_replay():
    create_starting_pieces()  # creates normal initial setup

    # Now apply moves up to replay_index
    for i in range(replay_index):
        apply_replay_move(replay_moves[i])


def draw_replay_controls():
    font = pygame.font.SysFont(None, 36)

    btn_prev = pygame.Rect(50, SCREEN_HEIGHT - 80, 100, 50)
    btn_next = pygame.Rect(200, SCREEN_HEIGHT - 80, 100, 50)
    btn_restart = pygame.Rect(350, SCREEN_HEIGHT - 80, 150, 50)
    btn_exit = pygame.Rect(550, SCREEN_HEIGHT - 80, 100, 50)

    pygame.draw.rect(screen, (100, 100, 200), btn_prev)
    pygame.draw.rect(screen, (100, 100, 200), btn_next)
    pygame.draw.rect(screen, (200, 100, 100), btn_restart)
    pygame.draw.rect(screen, (200, 50, 50), btn_exit)

    screen.blit(font.render("Prev", True, (255, 255, 255)),
                (btn_prev.x + 20, btn_prev.y + 10))
    screen.blit(font.render("Next", True, (255, 255, 255)),
                (btn_next.x + 20, btn_next.y + 10))
    screen.blit(font.render("Restart", True, (255, 255, 255)),
                (btn_restart.x + 20, btn_restart.y + 10))
    screen.blit(font.render("Exit", True, (255, 255, 255)),
                (btn_exit.x + 20, btn_exit.y + 10))

    return btn_prev, btn_next, btn_restart, btn_exit


def draw_menu():
    global menu_buttons
    menu_width = int(400 * MENU_SCALE)
    menu_height = int(300 * MENU_SCALE)
    menu_x = (SCREEN_WIDTH - menu_width) // 2
    menu_y = (SCREEN_HEIGHT - menu_height) // 2

    pygame.draw.rect(screen, (200, 200, 200), (menu_x, menu_y, menu_width, menu_height))
    pygame.draw.rect(screen, (100, 100, 100), (menu_x, menu_y, menu_width, menu_height), 4)

    font_size = int(36 * MENU_SCALE)
    menu_font = pygame.font.SysFont(None, font_size)
    title = menu_font.render("Settings", True, (0, 0, 0))
    screen.blit(title, (menu_x + menu_width // 2 - title.get_width() // 2, menu_y + int(20 * MENU_SCALE)))

    # Close button
    btn_w, btn_h = int(30 * MENU_SCALE), int(30 * MENU_SCALE)
    btn_x, btn_y = int(menu_x + menu_width - (40 * MENU_SCALE)), int(menu_y + 10 * MENU_SCALE)
    close_button = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
    pygame.draw.rect(screen, (255, 0, 0), close_button)
    close_text = menu_font.render("X", True, (255, 255, 255))
    screen.blit(close_text, (close_button.centerx - close_text.get_width() // 2,
                             close_button.centery - close_text.get_height() // 2))

    # Easy AI button
    easy_button = pygame.Rect(menu_x + 50, menu_y + 100, 100, 40)
    color_easy = (150, 220, 150) if AI_DIFFICULTY == "EASY" else (100, 200, 100)  # highlight selected
    pygame.draw.rect(screen, color_easy, easy_button)
    screen.blit(menu_font.render("Easy", True, (0, 0, 0)), (easy_button.x + 10, easy_button.y + 5))

    # Hard AI button
    hard_button = pygame.Rect(menu_x + 50, menu_y + 160, 100, 40)
    color_hard = (220, 150, 150) if AI_DIFFICULTY == "HARD" else (200, 100, 100)  # highlight selected
    pygame.draw.rect(screen, color_hard, hard_button)
    screen.blit(menu_font.render("Hard", True, (0, 0, 0)), (hard_button.x + 10, hard_button.y + 5))

    # Store buttons in global dict
    menu_buttons["close"] = close_button
    menu_buttons["easy"] = easy_button
    menu_buttons["hard"] = hard_button


def draw_ui_buttons():
    button_w = 120
    button_h = 50
    padding = 20

    # Menu button
    menu_button = pygame.Rect(padding, padding, button_w, button_h)

    # Reset button
    reset_button = pygame.Rect(padding * 2 + button_w, padding, button_w, button_h)

    # Replay button (added)
    replay_button = pygame.Rect(padding * 3 + button_w * 2, padding, button_w, button_h)

    # Menu button
    pygame.draw.rect(screen, (50, 50, 150), menu_button)
    pygame.draw.rect(screen, (100, 100, 200), menu_button, 2)
    menu_text = font.render("Menu", True, (255, 255, 255))
    screen.blit(menu_text, (menu_button.centerx - menu_text.get_width() // 2,
                            menu_button.centery - menu_text.get_height() // 2))

    # Reset button
    pygame.draw.rect(screen, (150, 50, 50), reset_button)
    pygame.draw.rect(screen, (200, 100, 100), reset_button, 2)
    reset_text = font.render("Reset", True, (255, 255, 255))
    screen.blit(reset_text, (reset_button.centerx - reset_text.get_width() // 2,
                             reset_button.centery - reset_text.get_height() // 2))

    # Replay button
    pygame.draw.rect(screen, (50, 150, 50), replay_button)
    pygame.draw.rect(screen, (100, 200, 100), replay_button, 2)
    replay_text = font.render("Replay", True, (255, 255, 255))
    screen.blit(replay_text, (replay_button.centerx - replay_text.get_width() // 2,
                              replay_button.centery - replay_text.get_height() // 2))

    return menu_button, reset_button, replay_button


def scale_window(new_size):
    global SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, BOARD_SIZE, BOARD_OFFSET_X, BOARD_OFFSET_Y
    global screen, board_state, UI_SPACE_HEIGHT, UI_SCALE, MENU_SCALE

    # Save old board info before resizing
    old_tile = TILE_SIZE
    old_offset_x = BOARD_OFFSET_X
    old_ui_height = UI_SPACE_HEIGHT

    # Update screen size
    SCREEN_WIDTH, SCREEN_HEIGHT = new_size
    SCREEN_HEIGHT = max(SCREEN_HEIGHT, 400)  # minimum playable size

    # Calculate scaling ratios for UI and menu
    base_width = 800
    UI_SCALE = SCREEN_WIDTH / base_width
    MENU_SCALE = SCREEN_WIDTH / base_width

    # scale UI bar height
    UI_SPACE_HEIGHT = int(60 * UI_SCALE)
    UI_SPACE_HEIGHT = max(UI_SPACE_HEIGHT, 40)  # avoid too thin a bar

    # Calculate new board scaling
    side = min(SCREEN_WIDTH, SCREEN_HEIGHT - UI_SPACE_HEIGHT)
    TILE_SIZE = side // 8
    BOARD_SIZE = TILE_SIZE * 8
    BOARD_OFFSET_X = (SCREEN_WIDTH - BOARD_SIZE) // 2
    BOARD_OFFSET_Y = UI_SPACE_HEIGHT

    # Recreate screen
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)

    # Rescale penguin sprites to the new tile size
    rescale_penguin_images()

    # Update piece locations
    for piece in board_state:
        x, y = piece.location

        old_col = int((x - old_offset_x) // old_tile)
        old_row = int((y - old_ui_height) // old_tile)  # original UI bar was 60 tall

        if 0 <= old_row < ROWS and 0 <= old_col < ROWS:
            new_x = BOARD_OFFSET_X + old_col * TILE_SIZE + TILE_SIZE // 2
            new_y = UI_SPACE_HEIGHT + old_row * TILE_SIZE + TILE_SIZE // 2

            piece.location = (new_x, new_y)
            piece.radius = TILE_SIZE // 3

            piece.update_rect()

    # redraq immediately
    pygame.display.flip()


def save_game_state():
    print()


# add anything here you want to call whenever a turn ends
def on_turn_end():
    check_game_over()
    save_game_state()
    # print(board_state)


def logic_board():
    board = [[None for _ in range(8)] for _ in range(8)]
    for p in board_state:
        r, c = pixel_to_board(p.location)
        if p.king:
            board[r][c] = ("Wk" if p.player == WHITE else "Bk")
        else:
            board[r][c] = ("W" if p.player == WHITE else "B")


def get_all_player_moves(player_color):
    moves = []
    forced = get_forced_jump_pieces(player_color)

    pieces = forced if forced else [p for p in board_state if p.player == player_color]
    for p in pieces:
        valid = get_valid_moves(p, only_jumps=bool(forced))
        for (r, c) in valid:
            moves.append((p, (r, c)))
    return moves


def apply_ai_move(ai):
    global turn, selected_piece, valid_moves, jump_occurred, multi_jump
    global turn
    result = ai.pick_move()
    if not result:
        return
    piece, (r, c) = result

    sr, sc = pixel_to_board(piece.location)
    dr, dc = r - sr, c - sc

    if abs(dr) == 2:
        jumped = piece_at(sr + dr // 2, sc + dc // 2)
        if jumped:
            board_state.remove(jumped)

    piece.update_location(board_to_pixel(r, c))
    sr2, sc2 = pixel_to_board(piece.location)
    turn += 1
    on_turn_end()


# -----------------------------
# USER ACCOUNT SYSTEM
# -----------------------------

USERS_FILE = "users.json"
current_user = None


def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def register_user(username, password):
    users = load_users()
    if username in users:
        return False, "Username already exists."
    users[username] = hash_password(password)
    save_users(users)
    return True, "Registration successful!"


def verify_login(username, password):
    users = load_users()
    if username not in users:
        return False, "User does not exist."
    if users[username] != hash_password(password):
        return False, "Incorrect password."
    return True, "Login successful!"


def save_game_record():
    if not move_history:
        return

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"games/{current_user}_{timestamp}.json"

    record = {
        "white_player": player1_user,
        "black_player": player2_user,
        "timestamp": timestamp,
        "moves": move_history
    }

    with open(filename, "w") as f:
        json.dump(record, f, indent=4)

    print(f"Game saved to {filename}")


# -----------------------------
# Game Loop Setup
# -----------------------------
# Create initial board setup with pieces
create_starting_pieces()

# Initialize control variables
running = True
selected_piece = None
valid_moves = []
dragging = False
orig_pos = None
multi_jump = False
hover_piece = None
jump_occurred = False
font = pygame.font.SysFont(None, 36)  # Font for text display

# -----------------------------
# Main Game Loop
# -----------------------------
if __name__ =="__main__":
    running = True

    while running:
        clock.tick(60)
        mouse_pos = pygame.mouse.get_pos()

        # -----------------------------
        # EVENT HANDLING
        # -----------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                scale_window(event.size)

            # -----------------------------
            # LOGIN SCREEN
            # -----------------------------
            if login_screen_active:
                submit_btn, user_box, pass_box, switch_box = draw_login_screen()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Check if user clicked on username/password boxes
                    if user_box.collidepoint(event.pos):
                        input_active = "username"
                    elif pass_box.collidepoint(event.pos):
                        input_active = "password"
                    # Check submit button
                    elif submit_btn.collidepoint(event.pos):
                        ok, msg = verify_login(login_username, login_password)
                        login_message = msg
                        if ok:
                            if login_stage == "P1":
                                player1_user = login_username
                                login_stage = "P2" if game_mode == "PVP" else "DONE"
                                login_username = ""
                                login_password = ""
                            elif login_stage == "P2":
                                player2_user = login_username
                                login_stage = "DONE"
                                login_username = ""
                                login_password = ""

                            if login_stage == "DONE":
                                login_screen_active = False

                elif event.type == pygame.KEYDOWN:
                    if input_active == "username":
                        if event.key == pygame.K_BACKSPACE:
                            login_username = login_username[:-1]
                        else:
                            login_username += event.unicode
                    elif input_active == "password":
                        if event.key == pygame.K_BACKSPACE:
                            login_password = login_password[:-1]
                        else:
                            login_password += event.unicode

            # -----------------------------
            # MODE SELECT SCREEN
            # -----------------------------
            elif mode_select_active:
                btn_pvp, btn_easy, btn_hard = draw_mode_select()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_pvp.collidepoint(event.pos):
                        game_mode = "PVP"
                    elif btn_easy.collidepoint(event.pos):
                        game_mode = "AI_EASY"
                        player2_user = "AI_Bot"
                        AI_DIFFICULTY = "EASY"
                    elif btn_hard.collidepoint(event.pos):
                        game_mode = "AI_HARD"
                        player2_user = "AI_Bot"
                        AI_DIFFICULTY = "HARD"

                    mode_select_active = False
                    if game_mode.startswith("AI") or game_mode == "PVP":
                        login_screen_active = True
                        login_stage = "P1"
                        login_username = ""
                        login_password = ""

            # -----------------------------
            # REPLAY FILE SELECT MODE
            # -----------------------------
            elif replay_file_select_active:
                file_buttons = draw_replay_file_select()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for rect, fname in file_buttons:
                        if rect.collidepoint(event.pos):
                            load_replay_file(fname)
                            replay_mode_active = True
                            replay_file_select_active = False
                            reset_board_for_replay()

            # -----------------------------
            # REPLAY MODE
            # -----------------------------
            elif replay_mode_active:
                btn_prev, btn_next, btn_restart, btn_exit = draw_replay_controls()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_prev.collidepoint(event.pos) and replay_index > 0:
                        replay_index -= 1
                        reset_board_for_replay()
                    elif btn_next.collidepoint(event.pos) and replay_index < replay_total:
                        apply_replay_move(replay_moves[replay_index])
                        replay_index += 1
                    elif btn_restart.collidepoint(event.pos):
                        replay_index = 0
                        reset_board_for_replay()
                    elif btn_exit.collidepoint(event.pos):
                        replay_mode_active = False
                        reset_game()

            # -----------------------------
            # NORMAL GAMEPLAY
            # -----------------------------
            else:
                # SETTINGS MENU
                if show_menu:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if menu_buttons["close"].collidepoint(mouse_pos):
                            show_menu = False
                        elif menu_buttons["easy"].collidepoint(mouse_pos):
                            AI_DIFFICULTY = "EASY"
                        elif menu_buttons["hard"].collidepoint(mouse_pos):
                            AI_DIFFICULTY = "HARD"
                    continue

                # UI BUTTONS
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    menu_button, reset_button, replay_button = draw_ui_buttons()
                    if replay_button.collidepoint(mouse_pos):
                        replay_file_select_active = True
                        break
                    if menu_button.collidepoint(mouse_pos):
                        show_menu = True
                        break
                    elif reset_button.collidepoint(mouse_pos):
                        reset_game()
                        break

                # PIECE SELECTION
                if not selected_piece and not game_over:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        for piece in board_state:
                            if piece.clicked(mouse_pos) and piece.player == get_current_turn():
                                forced = get_forced_jump_pieces(get_current_turn())
                                if forced and piece not in forced:
                                    continue
                                only_jumps = bool(forced) or jump_occurred
                                moves = get_valid_moves(piece, only_jumps)
                                if moves:
                                    selected_piece = piece
                                    valid_moves = moves
                                    dragging = True
                                    orig_pos = piece.location
                                    break

                # DRAGGING
                if event.type == pygame.MOUSEMOTION and dragging and selected_piece:
                    selected_piece.update_location(mouse_pos)

                # DROP PIECE
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and dragging:
                    dragging = False
                    if selected_piece:
                        row, col = pixel_to_board(mouse_pos)
                        sr, sc = pixel_to_board(orig_pos)
                        dr, dc = row - sr, col - sc
                        if (row, col) in valid_moves:
                            is_jump = abs(dr) == 2
                            move_history.append(algebraic_move(sr, sc, row, col, is_jump))
                            if is_jump:
                                jumped = piece_at(sr + dr // 2, sc + dc // 2)
                                if jumped:
                                    board_state.remove(jumped)
                                selected_piece.update_location(board_to_pixel(row, col))
                                jump_occurred = True
                                multi_jump = get_valid_moves(selected_piece, True)
                                if multi_jump:
                                    valid_moves = multi_jump
                                    orig_pos = selected_piece.location
                                    dragging = True
                                else:
                                    selected_piece = None
                                    valid_moves = []
                                    multi_jump = False
                                    jump_occurred = False
                                    turn += 1
                                    on_turn_end()
                            else:
                                if jump_occurred:
                                    selected_piece.update_location(orig_pos)
                                else:
                                    selected_piece.update_location(board_to_pixel(row, col))
                                    selected_piece = None
                                    valid_moves = []
                                    turn += 1
                                    on_turn_end()
                        else:
                            selected_piece.update_location(orig_pos)
                            selected_piece = None
                            valid_moves = []

                # AI TURN
                if game_mode in ("AI_EASY", "AI_HARD") and not dragging and not game_over and turn % 2 == 1:
                    ai = easy_AI(BLACK) if game_mode == "AI_EASY" else hard_AI(BLACK)
                    apply_ai_move(ai)

        # -----------------------------
        # DRAWING
        # -----------------------------
        screen.fill((0, 0, 0))
        if login_screen_active:
            draw_login_screen()
        elif mode_select_active:
            draw_mode_select()
        elif replay_file_select_active:
            draw_replay_file_select()
        elif replay_mode_active:
            draw_replay_controls()
            draw_board()
            draw_all_pieces()
        else:
            draw_ui_buttons()
            draw_ai_difficulty()
            if show_menu:
                draw_menu()
            else:
                draw_board()
                draw_all_pieces()
                # Highlight forced pieces
                for piece in get_forced_jump_pieces(get_current_turn()):
                    pygame.draw.circle(screen, HIGHLIGHT_YELLOW, piece.location, piece.radius + 5, 4)
                # Highlight valid moves
                if selected_piece:
                    for r, c in valid_moves:
                        pygame.draw.circle(screen, HIGHLIGHT_YELLOW, board_to_screen_pixel(r, c), TILE_SIZE // 6)
                    pygame.draw.circle(screen, HIGHLIGHT_RED, selected_piece.location, selected_piece.radius + 5, 3)
                # Game over overlay
                if game_over:
                    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                    overlay.set_alpha(180)
                    overlay.fill((0, 0, 0))
                    screen.blit(overlay, (0, 0))
                    game_over_text = font.render(f"Game over, {game_winner} wins!", True, (255, 255, 255))
                    screen.blit(game_over_text, ((SCREEN_WIDTH - game_over_text.get_width()) // 2,
                                                 (SCREEN_HEIGHT - game_over_text.get_height()) // 2))

        pygame.display.flip()

    pygame.quit()
