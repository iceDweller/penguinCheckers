import pygame
import time
import random

# ============================================================
#              INITIAL SETUP
# ============================================================

# Initialize Pygame so we can use all its built-in graphics functions
pygame.init()

# -----------------------------
# Window / Board Setup
# -----------------------------

# Height (in pixels) reserved at the top of the window for UI elements
UI_SPACE_HEIGHT = 60

# Get info about the user's current display (screen resolution)
info = pygame.display.Info()

# Choose window size:
# - Never larger than 800x800 (so it fits most screens)
# - Slightly smaller than the user's monitor so it doesn't cover everything
SCREEN_WIDTH = min(info.current_w - 100, 800)
SCREEN_HEIGHT = min(info.current_h - 100, 800) + UI_SPACE_HEIGHT

# Create a resizable window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Penguin Checkers")

# Buttons that appear inside the settings menu
menu_buttons = {
    "close": None,
    "easy": None,
    "hard": None
}

# AI difficulty setting (EASY or HARD)
AI_DIFFICULTY = "EASY"

# Scale factors used when the window is resized
UI_SCALE = 1.0
MENU_SCALE = 1.0

# -----------------------------
# Board Geometry
# -----------------------------

# Each checkerboard side is 8 squares
ROWS = 8

# Tile size (width/height of one square) based on current window
TILE_SIZE = min(SCREEN_WIDTH, SCREEN_HEIGHT) // ROWS

# Total board size in pixels (8 x TILE_SIZE)
BOARD_SIZE = TILE_SIZE * ROWS

# Board offset from the left/right edges (so the board is centered)
BOARD_OFFSET_X = (SCREEN_WIDTH - BOARD_SIZE) // 2

# Top offset for the board (we draw it under the UI bar)
BOARD_OFFSET_Y = 0  # board itself starts below UI_SPACE_HEIGHT in some functions

# -----------------------------
# Colors
# -----------------------------

# Board tile colors
BLUE_TILE = (0, 102, 204)     # Dark squares (blue)
WHITE_TILE = (255, 255, 255)  # Light squares (white)

# Piece base colors (still used for identifying players)
BLACK = (35, 35, 35)          # Black player pieces
BLACK_BORDER = (70, 70, 70)   # Outline for black pieces (for highlights)
WHITE = (255, 255, 255)       # White player pieces
WHITE_BORDER = (200, 200, 200)# Outline for white pieces (for highlights)

# Outline thickness around pieces
HIGHLIGHT_WIDTH = 5

# Highlight / effect colors
HIGHLIGHT_YELLOW = (255, 255, 0)  # Valid move dots / forced jump outline
HIGHLIGHT_GREEN = (0, 255, 0)     # Hover highlight
HIGHLIGHT_RED = (255, 0, 0)       # Selected piece highlight
HIGHLIGHT_GOLD = (255, 215, 0)    # (Still available if you ever want extra gold effects)

# Clock object to control frames-per-second (FPS)
clock = pygame.time.Clock()

# -----------------------------
# Penguin piece images
# -----------------------------

# Load base images with alpha so transparency is preserved
BLACK_PENGUIN_BASE = pygame.image.load("BlackPenguinPiece.png").convert_alpha()
WHITE_PENGUIN_BASE = pygame.image.load("WhitePenguinPiece.png").convert_alpha()
BLACK_PENGUIN_KING_BASE = pygame.image.load("BlackPenguinKingPiece.png").convert_alpha()
WHITE_PENGUIN_KING_BASE = pygame.image.load("WhitePenguinKingPiece.png").convert_alpha()

# These will hold the scaled images that match the current TILE_SIZE
BLACK_PENGUIN_IMG = None
WHITE_PENGUIN_IMG = None
BLACK_PENGUIN_KING_IMG = None
WHITE_PENGUIN_KING_IMG = None


def rescale_penguin_images():
    """Resize penguin images whenever TILE_SIZE changes."""
    global BLACK_PENGUIN_IMG, WHITE_PENGUIN_IMG
    global BLACK_PENGUIN_KING_IMG, WHITE_PENGUIN_KING_IMG

    size = int(TILE_SIZE * 0.9)  # a bit smaller than the tile

    BLACK_PENGUIN_IMG = pygame.transform.smoothscale(
        BLACK_PENGUIN_BASE, (size, size)
    )
    WHITE_PENGUIN_IMG = pygame.transform.smoothscale(
        WHITE_PENGUIN_BASE, (size, size)
    )
    BLACK_PENGUIN_KING_IMG = pygame.transform.smoothscale(
        BLACK_PENGUIN_KING_BASE, (size, size)
    )
    WHITE_PENGUIN_KING_IMG = pygame.transform.smoothscale(
        WHITE_PENGUIN_KING_BASE, (size, size)
    )


# Initial scale of the piece images
rescale_penguin_images()

# ============================================================
#              GAME STATE VARIABLES
# ============================================================

# List of all Checker objects currently on the board
board_state = []

# Optional: can be used for storing past board positions (undo, replay, etc.)
board_history = []

# Turn number (even = White's turn, odd = Black's turn)
turn = 0

# Piece currently picked up/selected by the player (Checker instance or None)
selected_piece = None

# List of valid (row, col) moves for the selected piece
valid_moves = []

# True while the mouse is dragging a piece
dragging = False

# Original pixel position of a piece before the drag started
orig_pos = None

# Used if we wanted to implement offset dragging (currently unused)
offset_x = offset_y = 0

# True if the current move sequence is in the middle of a multi-jump
multi_jump = False

# True if any jump occurred during this turn
jump_occurred = False

# Flags for game end
game_over = False
game_winner = None

# True when the settings menu is open
show_menu = False

# Piece currently under the mouse cursor (for hover highlight)
hover_piece = None

# ============================================================
#              CHECKER PIECE CLASS
# ============================================================

class Checker:
    # Represents a single checker piece on the board.
    # Handles position, drawing, king promotion, and click detection.
    def __init__(self, location, status, player):
        # location is a (x, y) pixel position of the center of the sprite
        self.location = location
        self.status = status       # "normal" or "king"
        self.player = player       # color tuple (WHITE or BLACK)
        self.king = False          # becomes True when piece is promoted
        self.radius = TILE_SIZE // 3  # still used for highlight circles

        # White moves "up" (-1 row), Black moves "down" (+1 row)
        self.direction = -1 if player == WHITE else 1

        # Create the clickable rectangle for this piece
        self.update_rect()

    def update_location(self, new_location):
        # Move the piece to a new pixel location,
        # then check if it should be promoted to king.
        self.location = new_location
        self.update_rect()

        # Check promotion based on final row
        r, _ = pixel_to_board(new_location)
        if not self.king:
            if self.player == WHITE and r == 0:
                self.make_king()
            elif self.player == BLACK and r == ROWS - 1:
                self.make_king()

    def update_rect(self):
        # Update the rectangle used to detect mouse clicks on this piece.
        size = int(TILE_SIZE * 0.9)
        rect = pygame.Rect(0, 0, size, size)
        rect.center = self.location
        self.rect = rect

    def make_king(self):
        # Turn this piece into a king and allow it to move in both directions.
        self.king = True
        self.direction = 0   # 0 means: use all four diagonals
        self.status = "king"

    def draw_self(self):
        # Draw the penguin sprite at this piece's location.
        # Uses different images for normal vs king pieces.
        if self.player == WHITE:
            img = WHITE_PENGUIN_KING_IMG if self.king else WHITE_PENGUIN_IMG
        else:
            img = BLACK_PENGUIN_KING_IMG if self.king else BLACK_PENGUIN_IMG

        rect = img.get_rect(center=self.location)
        screen.blit(img, rect)

    def clicked(self, mouse_pos):
        # Return True if the given mouse position is inside the piece's rect.
        return self.rect.collidepoint(mouse_pos)

# ============================================================
#              AI CLASSES
# ============================================================

class easy_AI:
    # AI that simply chooses a random legal move.
    def __init__(self, color):
        self.color = color

    def pick_move(self):
        # Get all allowed moves for this color
        moves = get_all_player_moves(self.color)
        if not moves:
            return None
        # Randomly choose (piece, (row, col)) from the move list
        piece, (r, c) = random.choice(moves)
        return piece, (r, c)


class hard_AI:
    # Slightly smarter AI that scores each possible move and chooses the one with the highest score.
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

        # Sort by score (highest first) and pick the first move
        scored_moves.sort(reverse=True, key=lambda x: x[0])
        _, piece, move = scored_moves[0]
        return piece, move

    def evaluate_move(self, piece, r, c):
        # Give a numeric score to a potential move. Bigger score = better move.
        sr, sc = pixel_to_board(piece.location)
        dr = r - sr
        score = 0

        # Reward moving pieces forward toward king promotion
        if piece.player == BLACK:
            score += dr
        else:
            score -= dr

        # Big reward for getting a king
        if piece.player == BLACK and r == ROWS - 1:
            score += 10
        elif piece.player == WHITE and r == 0:
            score += 10

        # Reward captures (jumps)
        if abs(dr) == 2:
            score += 5

        # Small reward for occupying the center of the board
        if 2 <= r <= 5 and 2 <= c <= 5:
            score += 1

        # Tiny random factor so the AI doesn't always behave identically
        score += random.uniform(0, 0.5)

        return score

# ============================================================
#              HELPER FUNCTIONS
# ============================================================

def get_current_turn():
    # Return the color whose turn it currently is (WHITE or BLACK).
    return WHITE if turn % 2 == 0 else BLACK


def pixel_to_board(pos):
    # Convert a pixel position (x, y) on the screen into board coordinates (row, col).
    # Returns (-1, -1) if the position is outside the board.
    x, y = pos
    board_x = x - BOARD_OFFSET_X
    board_y = y - UI_SPACE_HEIGHT

    if 0 <= board_x < BOARD_SIZE and 0 <= board_y < BOARD_SIZE:
        col = int(board_x // TILE_SIZE)
        row = int(board_y // TILE_SIZE)
        return row, col
    return -1, -1


def draw_ai_difficulty():
    # Draw text in the UI bar showing the current AI difficulty.
    ui_font = pygame.font.SysFont(None, int(24 * UI_SCALE))
    text = ui_font.render(f"AI Difficulty: {AI_DIFFICULTY}", True, (255, 255, 255))
    screen.blit(text, (SCREEN_WIDTH - 250, int(10 * UI_SCALE)))


def board_to_pixel(row, col):
    # Convert board (row, col) back into a pixel center (x, y).
    x = BOARD_OFFSET_X + col * TILE_SIZE + TILE_SIZE // 2
    y = UI_SPACE_HEIGHT + row * TILE_SIZE + TILE_SIZE // 2
    return (x, y)


def board_to_screen_pixel(row, col):
    # Same as board_to_pixel. Kept separate for clarity when used in drawing.
    x = BOARD_OFFSET_X + col * TILE_SIZE + TILE_SIZE // 2
    y = UI_SPACE_HEIGHT + row * TILE_SIZE + TILE_SIZE // 2
    return (x, y)


def is_dark_square(r, c):
    # Return True if the board square at (r, c) is a dark square.
    return (r + c) % 2 != 0


def piece_at(row, col):
    # Return the Checker located at board (row, col), or None if no piece is there.
    for p in board_state:
        pr, pc = pixel_to_board(p.location)
        if pr == row and pc == col:
            return p
    return None


def create_starting_pieces():
    # Clear the board_state list and re-place all pieces into their starting positions.
    board_state.clear()

    for r in range(ROWS):
        for c in range(ROWS):
            # Pieces only sit on dark squares
            if not is_dark_square(r, c):
                continue

            x, y = board_to_pixel(r, c)

            # Black pieces occupy the top 3 rows (0,1,2)
            if r < 3:
                board_state.append(Checker((x, y), "normal", BLACK))
            # White pieces occupy the bottom 3 rows (5,6,7)
            elif r > 4:
                board_state.append(Checker((x, y), "normal", WHITE))


def draw_board():
    # Draw the 8x8 blue/white checkerboard.
    for row in range(ROWS):
        for col in range(ROWS):
            x = BOARD_OFFSET_X + col * TILE_SIZE
            y = UI_SPACE_HEIGHT + row * TILE_SIZE
            color = WHITE_TILE if (row + col) % 2 == 0 else BLUE_TILE
            pygame.draw.rect(screen, color, (x, y, TILE_SIZE, TILE_SIZE))


def draw_all_pieces():
    # Draw every Checker object currently in board_state.
    for p in board_state:
        p.draw_self()


def get_valid_moves(piece, only_jumps=False):
    # Compute all valid moves for a given piece.
    # Returns a list of (row, col) positions.
    # - If only_jumps is True, only jump moves are returned.
    # - If there are any jump moves, they take priority over normal moves.
    moves = []
    r, c = pixel_to_board(piece.location)

    # Kings move in all four diagonal directions; normal pieces move "forward".
    if piece.king:
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    else:
        directions = [(piece.direction, -1), (piece.direction, 1)]

    jumps = []

    for dr, dc in directions:
        nr, nc = r + dr, c + dc

        # Ensure the target square is on the board and is a dark square
        if 0 <= nr < ROWS and 0 <= nc < ROWS and is_dark_square(nr, nc):
            target = piece_at(nr, nc)

            # Normal move (empty square, no forced jumps active)
            if not target and not only_jumps:
                moves.append((nr, nc))

            # Check if a jump move is possible (skip over opponent)
            jr, jc = r + dr * 2, c + dc * 2
            if 0 <= jr < ROWS and 0 <= jc < ROWS and is_dark_square(jr, jc):
                jumped = piece_at(nr, nc)
                if jumped and jumped.player != piece.player and not piece_at(jr, jc):
                    jumps.append((jr, jc))

    # If any jumps exist, they are the only legal moves
    return jumps if jumps else moves


def get_forced_jump_pieces(player_color):
    # Return a list of pieces for player_color that currently have at least one jump move.
    # If this list is non-empty, that player MUST choose one of these pieces.
    pieces = [p for p in board_state if p.player == player_color]
    jump_pieces = []
    for piece in pieces:
        jump_moves = get_valid_moves(piece, only_jumps=True)
        if jump_moves:
            jump_pieces.append(piece)
    return jump_pieces


def reset_game():
    # Reset all game state variables so the game starts fresh.
    global turn, selected_piece, valid_moves, dragging
    global orig_pos, multi_jump, jump_occurred, hover_piece, game_over, game_winner, board_history

    create_starting_pieces()
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


def check_game_over():
    # Check if the game is finished.
    # Conditions:
    #   - One side has no pieces left.
    #   - Current player has no legal moves.
    # Returns True if the game ended, False otherwise.
    global game_over, game_winner

    # Count pieces for each side
    white_pieces = [p for p in board_state if p.player == WHITE]
    black_pieces = [p for p in board_state if p.player == BLACK]

    # Win by capturing all opponent pieces
    if len(white_pieces) == 0:
        game_over = True
        game_winner = "BLACK"
        return True
    if len(black_pieces) == 0:
        game_over = True
        game_winner = "WHITE"
        return True

    # Check if current player has any legal moves left
    current_player_pieces = [p for p in board_state if p.player == get_current_turn()]
    has_valid_move = any(get_valid_moves(piece) for piece in current_player_pieces)

    # No legal moves = player is stuck and loses
    if not has_valid_move:
        game_over = True
        game_winner = "BLACK" if get_current_turn() == WHITE else "WHITE"
        return True

    return False


def draw_menu():
    # Draw the settings popup in the middle of the screen.
    # Stores Rects for close/easy/hard buttons into menu_buttons.
    global menu_buttons

    menu_width = int(400 * MENU_SCALE)
    menu_height = int(300 * MENU_SCALE)
    menu_x = (SCREEN_WIDTH - menu_width) // 2
    menu_y = (SCREEN_HEIGHT - menu_height) // 2

    # Menu background
    pygame.draw.rect(screen, (200, 200, 200), (menu_x, menu_y, menu_width, menu_height))
    pygame.draw.rect(screen, (100, 100, 100), (menu_x, menu_y, menu_width, menu_height), 4)

    # Title
    font_size = int(36 * MENU_SCALE)
    menu_font = pygame.font.SysFont(None, font_size)
    title = menu_font.render("Settings", True, (0, 0, 0))
    screen.blit(
        title,
        (menu_x + menu_width // 2 - title.get_width() // 2,
         menu_y + int(20 * MENU_SCALE))
    )

    # Close (X) button
    btn_w, btn_h = int(30 * MENU_SCALE), int(30 * MENU_SCALE)
    btn_x, btn_y = int(menu_x + menu_width - (40 * MENU_SCALE)), int(menu_y + 10 * MENU_SCALE)
    close_button = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
    pygame.draw.rect(screen, (255, 0, 0), close_button)
    close_text = menu_font.render("X", True, (255, 255, 255))
    screen.blit(
        close_text,
        (close_button.centerx - close_text.get_width() // 2,
         close_button.centery - close_text.get_height() // 2)
    )

    # Easy AI button
    easy_button = pygame.Rect(menu_x + 50, menu_y + 100, 100, 40)
    color_easy = (150, 220, 150) if AI_DIFFICULTY == "EASY" else (100, 200, 100)
    pygame.draw.rect(screen, color_easy, easy_button)
    screen.blit(
        menu_font.render("Easy", True, (0, 0, 0)),
        (easy_button.x + 10, easy_button.y + 5)
    )

    # Hard AI button
    hard_button = pygame.Rect(menu_x + 50, menu_y + 160, 100, 40)
    color_hard = (220, 150, 150) if AI_DIFFICULTY == "HARD" else (200, 100, 100)
    pygame.draw.rect(screen, color_hard, hard_button)
    screen.blit(
        menu_font.render("Hard", True, (0, 0, 0)),
        (hard_button.x + 10, hard_button.y + 5)
    )

    # Store button rectangles for event handling
    menu_buttons["close"] = close_button
    menu_buttons["easy"] = easy_button
    menu_buttons["hard"] = hard_button


def draw_ui_buttons():
    # Draw the top UI bar: turn indicator + Menu button + Reset button.
    # Returns (menu_button_rect, reset_button_rect).
    pygame.draw.rect(screen, (50, 50, 50), (0, 0, SCREEN_WIDTH, UI_SPACE_HEIGHT))
    pygame.draw.rect(screen, (100, 100, 100), (0, 0, SCREEN_WIDTH, UI_SPACE_HEIGHT), 4)

    font_size = int(36 * UI_SCALE)
    ui_font = pygame.font.SysFont(None, font_size)

    # "Turn: White" or "Turn: Black"
    turn_text = ui_font.render(f"Turn: {'White' if turn % 2 == 0 else 'Black'}", True, (255, 255, 255))
    screen.blit(turn_text, (int(10 * UI_SCALE), int(10 * UI_SCALE)))

    # Buttons on the right side
    button_w = int(100 * UI_SCALE)
    button_h = int(40 * UI_SCALE)
    padding = int(10 * UI_SCALE)

    menu_button = pygame.Rect(SCREEN_WIDTH - (button_w * 2 + padding * 2),
                              padding, button_w, button_h)
    reset_button = pygame.Rect(SCREEN_WIDTH - (button_w + padding),
                               padding, button_w, button_h)

    # Menu button visuals
    pygame.draw.rect(screen, (50, 50, 150), menu_button)
    pygame.draw.rect(screen, (100, 100, 200), menu_button, 2)
    menu_text = ui_font.render("Menu", True, (255, 255, 255))
    screen.blit(
        menu_text,
        (menu_button.centerx - menu_text.get_width() // 2,
         menu_button.centery - menu_text.get_height() // 2)
    )

    # Reset button visuals
    pygame.draw.rect(screen, (150, 50, 50), reset_button)
    pygame.draw.rect(screen, (200, 100, 100), reset_button, 2)
    reset_text = ui_font.render("Reset", True, (255, 255, 255))
    screen.blit(
        reset_text,
        (reset_button.centerx - reset_text.get_width() // 2,
         reset_button.centery - reset_text.get_height() // 2)
    )

    return menu_button, reset_button


def scale_window(new_size):
    # Called when the user resizes the window.
    # Recomputes TILE_SIZE, board offsets, UI scaling, and rescales
    # all piece positions to keep them aligned to the grid.
    global SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, BOARD_SIZE, BOARD_OFFSET_X, BOARD_OFFSET_Y
    global screen, UI_SPACE_HEIGHT, UI_SCALE, MENU_SCALE

    # Save old board info before resizing
    old_tile = TILE_SIZE
    old_offset_x = BOARD_OFFSET_X
    old_ui_height = UI_SPACE_HEIGHT

    # Update screen size
    SCREEN_WIDTH, SCREEN_HEIGHT = new_size
    SCREEN_HEIGHT = max(SCREEN_HEIGHT, 400)  # minimum height for usability

    # Scale factors relative to 800px base width
    base_width = 800
    UI_SCALE = SCREEN_WIDTH / base_width
    MENU_SCALE = SCREEN_WIDTH / base_width

    # Adjust UI bar height to new scale (but keep at least 40px)
    UI_SPACE_HEIGHT = int(60 * UI_SCALE)
    UI_SPACE_HEIGHT = max(UI_SPACE_HEIGHT, 40)

    # Recompute board geometry
    side = min(SCREEN_WIDTH, SCREEN_HEIGHT - UI_SPACE_HEIGHT)
    TILE_SIZE = side // ROWS
    BOARD_SIZE = TILE_SIZE * ROWS
    BOARD_OFFSET_X = (SCREEN_WIDTH - BOARD_SIZE) // 2
    BOARD_OFFSET_Y = UI_SPACE_HEIGHT

    # Rescale penguin sprites to the new tile size
    rescale_penguin_images()

    # Recreate the display surface with the new size
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)

    # Reposition every piece based on the new board geometry
    for piece in board_state:
        x, y = piece.location

        # Convert old pixel position back to (row, col) using old tile size/offset
        old_col = int((x - old_offset_x) // old_tile)
        old_row = int((y - old_ui_height) // old_tile)

        if 0 <= old_row < ROWS and 0 <= old_col < ROWS:
            new_x = BOARD_OFFSET_X + old_col * TILE_SIZE + TILE_SIZE // 2
            new_y = UI_SPACE_HEIGHT + old_row * TILE_SIZE + TILE_SIZE // 2
            piece.location = (new_x, new_y)
            piece.radius = TILE_SIZE // 3
            piece.update_rect()

    pygame.display.flip()


def save_game_state():
    # Placeholder for saving board history (currently does nothing).
    pass


def on_turn_end():
    # Convenience function run whenever a turn is finished.
    # Currently checks for game over and optionally saves the state.
    check_game_over()
    save_game_state()


def logic_board():
    # Build and return a simple 8x8 matrix view of the board.
    # Each cell contains:
    #   None  -> empty
    #   "W"   -> white normal piece
    #   "B"   -> black normal piece
    #   "Wk"  -> white king
    #   "Bk"  -> black king
    board = [[None for _ in range(8)] for _ in range(8)]
    for p in board_state:
        r, c = pixel_to_board(p.location)
        if r == -1:
            continue
        if p.king:
            board[r][c] = ("Wk" if p.player == WHITE else "Bk")
        else:
            board[r][c] = ("W" if p.player == WHITE else "B")
    return board


def get_all_player_moves(player_color):
    # Return a list of all legal moves for the given color.
    # Each element is (piece, (row, col)).
    # If any forced jumps exist, only those moves are returned.
    moves = []
    forced = get_forced_jump_pieces(player_color)

    pieces = forced if forced else [p for p in board_state if p.player == player_color]
    for p in pieces:
        valid = get_valid_moves(p, only_jumps=bool(forced))
        for (r, c) in valid:
            moves.append((p, (r, c)))
    return moves


def apply_ai_move(ai):
    # Ask the AI object for a move, apply it to the board,
    # and advance the turn if a move is available.
    global turn
    result = ai.pick_move()
    if not result:
        return

    piece, (r, c) = result

    # Determine row/column difference between source and destination
    sr, sc = pixel_to_board(piece.location)
    dr, dc = r - sr, c - sc

    # Handle remove-captured-piece for jump moves
    if abs(dr) == 2:
        jumped = piece_at(sr + dr // 2, sc + dc // 2)
        if jumped:
            board_state.remove(jumped)

    piece.update_location(board_to_pixel(r, c))
    turn += 1
    on_turn_end()

# ============================================================
#              GAME LOOP SETUP
# ============================================================

# Place pieces into starting positions
create_starting_pieces()

# Initialize font for text drawing
font = pygame.font.SysFont(None, 36)

# Main loop control flag
running = True

# (These are re-declared for clarity, but already global above.)
selected_piece = None
valid_moves = []
dragging = False
orig_pos = None
multi_jump = False
hover_piece = None
jump_occurred = False

# ============================================================
#              MAIN GAME LOOP
# ============================================================

while running:
    # Make the loop run at a maximum of 60 frames per second
    clock.tick(60)

    # Current mouse position and equivalent board cell
    mouse_pos = pygame.mouse.get_pos()
    row, col = pixel_to_board(mouse_pos)

    # -----------------------------
    # Event Handling
    # -----------------------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Handle window resizing events
        if event.type == pygame.VIDEORESIZE:
            scale_window(event.size)

        # -----------------------------
        # Menu Events (when settings pop-up is open)
        # -----------------------------
        if show_menu:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Close button
                if menu_buttons["close"] and menu_buttons["close"].collidepoint(mouse_pos):
                    show_menu = False
                # Easy AI option
                elif menu_buttons["easy"] and menu_buttons["easy"].collidepoint(mouse_pos):
                    AI_DIFFICULTY = "EASY"
                # Hard AI option
                elif menu_buttons["hard"] and menu_buttons["hard"].collidepoint(mouse_pos):
                    AI_DIFFICULTY = "HARD"

        # -----------------------------
        # Gameplay Events (normal board interactions)
        # -----------------------------
        else:  # show_menu is False
            # Update which piece is currently hovered
            if event.type == pygame.MOUSEMOTION:
                hover_piece = None
                for piece in board_state:
                    if piece.clicked(mouse_pos):
                        hover_piece = piece
                        break

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # First, check clicks on UI buttons (Menu / Reset)
                menu_button, reset_button = draw_ui_buttons()
                if menu_button.collidepoint(mouse_pos):
                    show_menu = True
                    break
                elif reset_button.collidepoint(mouse_pos):
                    reset_game()
                    break

                # If no UI button was clicked, try to select a piece
                if not selected_piece and not game_over:
                    for piece in board_state:
                        # Only let the current player select their own pieces
                        if piece.clicked(mouse_pos) and piece.player == get_current_turn():
                            forced_pieces = get_forced_jump_pieces(get_current_turn())
                            # If jumps are available, you must select a jumping piece
                            if forced_pieces and piece not in forced_pieces:
                                continue
                            only_jumps = bool(forced_pieces) or jump_occurred
                            moves = get_valid_moves(piece, only_jumps=only_jumps)
                            if moves:
                                selected_piece = piece
                                valid_moves = moves
                                dragging = True
                                orig_pos = piece.location
                                break

            # While the mouse moves with button held, drag the selected piece
            if event.type == pygame.MOUSEMOTION and dragging and selected_piece:
                mx, my = mouse_pos
                selected_piece.update_location((mx, my))

            # When mouse button is released, attempt to drop the piece to a valid square
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and dragging:
                dragging = False
                if selected_piece:
                    row, col = pixel_to_board(mouse_pos)
                    sr, sc = pixel_to_board(orig_pos)
                    dr, dc = row - sr, col - sc

                    if (row, col) in valid_moves:
                        # Jump move (captures an opponent)
                        if abs(dr) == 2:
                            jumped = piece_at(sr + dr // 2, sc + dc // 2)
                            if jumped:
                                board_state.remove(jumped)
                            selected_piece.update_location(board_to_pixel(row, col))
                            jump_occurred = True

                            # See if another jump is possible (multi-jump)
                            multi_jump = get_valid_moves(selected_piece, only_jumps=True)
                            if multi_jump:
                                valid_moves = multi_jump
                                orig_pos = selected_piece.location
                                dragging = True  # continue dragging for the next jump
                            else:
                                # End of jumping chain, finish turn
                                selected_piece = None
                                valid_moves = []
                                multi_jump = False
                                jump_occurred = False
                                turn += 1
                                on_turn_end()
                        # Normal move (no capture)
                        else:
                            # If we already jumped this turn, normal move is not allowed
                            if jump_occurred:
                                selected_piece.update_location(orig_pos)
                            else:
                                selected_piece.update_location(board_to_pixel(row, col))
                                selected_piece = None
                                valid_moves = []
                                turn += 1
                                on_turn_end()
                    else:
                        # Dropped on an invalid square â†’ snap back
                        selected_piece.update_location(orig_pos)
                        selected_piece = None
                        valid_moves = []

            # AI's turn (Black). Only triggers when it's Black's turn,
            # game is not over, and the human is not dragging a piece.
            if not dragging and not game_over and turn % 2 == 1:
                if AI_DIFFICULTY == "EASY":
                    ai = easy_AI(BLACK)
                else:
                    ai = hard_AI(BLACK)
                apply_ai_move(ai)

    # ========================================================
    #              DRAWING SECTION
    # ========================================================

    # Clear the screen every frame
    screen.fill((0, 0, 0))

    # Draw UI bar and AI difficulty label
    draw_ui_buttons()
    draw_ai_difficulty()

    if show_menu:
        # Draw the settings pop-up on top of everything
        draw_menu()
    else:
        # Draw board and pieces
        draw_board()
        draw_all_pieces()

        # Highlight any pieces that are forced to jump (thick yellow outline)
        forced_pieces = get_forced_jump_pieces(get_current_turn())
        for piece in forced_pieces:
            pygame.draw.circle(screen, HIGHLIGHT_YELLOW, piece.location, piece.radius + 5, 4)

        # Draw yellow dots on each valid move for the selected piece
        if selected_piece:
            for r, c in valid_moves:
                screen_pos = board_to_screen_pixel(r, c)
                pygame.draw.circle(screen, HIGHLIGHT_YELLOW, screen_pos, TILE_SIZE // 6)

        # Green outline around the piece under the mouse (if not forced jump)
        if hover_piece and hover_piece not in forced_pieces:
            pygame.draw.circle(screen, HIGHLIGHT_GREEN, hover_piece.location, hover_piece.radius + 5, 3)

        # Red outline around the selected piece
        if selected_piece:
            pygame.draw.circle(screen, HIGHLIGHT_RED, selected_piece.location, selected_piece.radius + 5, 3)

        # If the game is over, overlay a dark screen and show a message
        if game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            game_over_text = font.render(f"Game over, {game_winner} wins!", True, (255, 255, 255))
            screen.blit(
                game_over_text,
                (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2,
                 SCREEN_HEIGHT // 2 - game_over_text.get_height() // 2)
            )

    # Push all drawing operations to the actual window
    pygame.display.flip()
# Quit Pygame when the loop ends
pygame.quit()
