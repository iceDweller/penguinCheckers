import pygame

# Initialize Pygame so we can use all its built-in graphics functions
pygame.init()

# -----------------------------
# Window / Board Setup
# -----------------------------
# Create an 800x800 window for the checkers game
screen = pygame.display.set_mode((800, 800))
pygame.display.set_caption("Penguin Checkers")  # Title of the game window

# The checkers board has 8 rows and 8 columns
ROWS = 8
TILE_SIZE = 100  # Each square is 100x100 pixels

# Define board colors (light and dark squares)
BLUE_TILE = (0, 102, 204)     # Dark squares (blue)
WHITE_TILE = (255, 255, 255)  # Light squares (white)

# Define piece colors
BLACK = (0, 0, 0)             # Black player pieces
WHITE = (255, 255, 255)       # White player pieces

# Define colors for highlights and effects
HIGHLIGHT_YELLOW = (255, 255, 0)  # Used for showing valid move options
HIGHLIGHT_GREEN = (0, 255, 0)     # Used for hovering
HIGHLIGHT_RED = (255, 0, 0)       # Used for selected pieces
HIGHLIGHT_GOLD = (255, 215, 0)    # Used for kings (gold center)

# Clock object to control how fast the game updates (60 FPS)
clock = pygame.time.Clock()

# -----------------------------
# Game state variables
# -----------------------------
# Lists to store each player's pieces
player_white_pieces = []
player_black_pieces = []

# Keep track of whose turn it is (white moves first)
current_turn = WHITE

# Variables used for selecting and moving pieces
selected_piece = None
valid_moves = []
dragging = False
orig_pos = None
offset_x = offset_y = 0
multi_jump = False

# -----------------------------
# Checker Class - represents one checker piece
# -----------------------------
class Checker:
    def __init__(self, location, status, player):
        self.location = location   # Current pixel position of the piece
        self.status = status       # "normal" or "king"
        self.player = player       # Which player this piece belongs to
        self.king = False          # Whether the piece is a king yet
        self.radius = 35           # Circle size for the piece
        # White pieces move up (-1), Black pieces move down (+1)
        self.direction = -1 if player == WHITE else 1
        self.update_rect()         # Define the clickable area

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
        """Draw the piece on the board (with gold center if king)."""
        pygame.draw.circle(screen, self.player, self.location, self.radius)
        if self.king:
            pygame.draw.circle(screen, HIGHLIGHT_GOLD, self.location, self.radius // 2)

    def clicked(self, mouse_pos):
        """Return True if the mouse clicked on this piece."""
        return self.rect.collidepoint(mouse_pos)

# -----------------------------
# Helper Functions
# -----------------------------
def pixel_to_board(pos):
    """Convert screen pixel coordinates to board row/column indexes."""
    x, y = pos
    return y // TILE_SIZE, x // TILE_SIZE

def board_to_pixel(row, col):
    """Convert board row/column back into pixel coordinates."""
    return (col * TILE_SIZE + TILE_SIZE // 2, row * TILE_SIZE + TILE_SIZE // 2)

def is_dark_square(r, c):
    """Return True if the given board square should be dark blue."""
    return (r + c) % 2 != 0

def piece_at(row, col):
    """Check if a piece exists at a specific board position."""
    for p in player_white_pieces + player_black_pieces:
        pr, pc = pixel_to_board(p.location)
        if pr == row and pc == col:
            return p
    return None

def create_starting_pieces():
    """Place the starting pieces for both players on dark squares."""
    player_white_pieces.clear()
    player_black_pieces.clear()

    for r in range(ROWS):
        for c in range(ROWS):
            # Pieces only sit on dark squares
            if not is_dark_square(r, c):
                continue

            x = c * TILE_SIZE + TILE_SIZE // 2
            y = r * TILE_SIZE + TILE_SIZE // 2

            # Black pieces occupy the top 3 rows
            if r < 3:
                player_black_pieces.append(Checker((x, y), "normal", BLACK))
            # White pieces occupy the bottom 3 rows
            elif r > 4:
                player_white_pieces.append(Checker((x, y), "normal", WHITE))

def draw_board():
    """Draw the 8x8 blue-and-white checkerboard."""
    for row in range(ROWS):
        for col in range(ROWS):
            color = WHITE_TILE if (row + col) % 2 == 0 else BLUE_TILE
            pygame.draw.rect(screen, color, (col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE))

def draw_all_pieces():
    """Draw all checker pieces currently on the board."""
    for piece in player_white_pieces + player_black_pieces:
        piece.draw_self()

def get_valid_moves(piece, only_jumps=False):
    """Find valid diagonal moves (and jumps) for a piece."""
    moves = []
    r, c = pixel_to_board(piece.location)

    # King can move all four directions; normal pieces move forward only
    if piece.king:
        directions = [(-1,-1), (-1,1), (1,-1), (1,1)]
    else:
        directions = [(piece.direction,-1), (piece.direction,1)]

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
    """Return a list of pieces that must jump (if jump moves exist)."""
    pieces = player_white_pieces if player_color == WHITE else player_black_pieces
    return [piece for piece in pieces if get_valid_moves(piece, only_jumps=True)]

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
# Main Game Loop - runs continuously until window is closed
# -----------------------------
while running:
    clock.tick(60)  # Run loop at 60 frames per second
    mouse_pos = pygame.mouse.get_pos()
    row, col = pixel_to_board(mouse_pos)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False  # Close game window

        # Hover highlight (shows green outline when cursor hovers over a piece)
        if event.type == pygame.MOUSEMOTION:
            hover_piece = None
            for piece in player_white_pieces + player_black_pieces:
                if piece.clicked(mouse_pos):
                    hover_piece = piece
                    break

        # Pick up a piece (left click)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not selected_piece:
                for piece in player_white_pieces + player_black_pieces:
                    # Only allow clicking on your own turn’s pieces
                    if piece.clicked(mouse_pos) and piece.player == current_turn:
                        forced_pieces = get_forced_jump_pieces(current_turn)
                        # Must jump if a jump is available
                        if forced_pieces and piece not in forced_pieces:
                            continue
                        only_jumps = bool(forced_pieces) or jump_occurred
                        moves = get_valid_moves(piece, only_jumps=only_jumps)
                        if moves:
                            selected_piece = piece
                            valid_moves = moves
                            dragging = True
                            orig_pos = piece.location
                            offset_x = piece.location[0] - mouse_pos[0]
                            offset_y = piece.location[1] - mouse_pos[1]
                            break

        # Drag piece with mouse
        if event.type == pygame.MOUSEMOTION and dragging and selected_piece:
            mx, my = mouse_pos
            selected_piece.update_location((mx + offset_x, my + offset_y))

        # Drop piece (when releasing mouse)
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and dragging:
            dragging = False
            if selected_piece:
                sr, sc = pixel_to_board(orig_pos)
                dr, dc = row - sr, col - sc

                # Check if move is valid
                if (row, col) in valid_moves:
                    # Handle jump moves
                    if abs(dr) == 2:
                        jumped = piece_at(sr + dr // 2, sc + dc // 2)
                        if jumped:
                            # Remove captured piece from the opponent's list
                            if jumped in player_white_pieces:
                                player_white_pieces.remove(jumped)
                            else:
                                player_black_pieces.remove(jumped)
                        # Move jumped piece to new location
                        selected_piece.update_location(board_to_pixel(row, col))
                        jump_occurred = True
                        # Check if more jumps are possible (multi-jump)
                        multi_jump = get_valid_moves(selected_piece, only_jumps=True)
                        if multi_jump:
                            valid_moves = multi_jump
                            orig_pos = selected_piece.location
                            dragging = True
                        else:
                            # Switch turns after last jump
                            selected_piece = None
                            valid_moves = []
                            multi_jump = False
                            jump_occurred = False
                            current_turn = BLACK if current_turn == WHITE else WHITE
                    else:
                        # Normal (non-jump) move
                        if jump_occurred:
                            selected_piece.update_location(orig_pos)
                        else:
                            selected_piece.update_location(board_to_pixel(row, col))
                            selected_piece = None
                            valid_moves = []
                            current_turn = BLACK if current_turn == WHITE else WHITE
                else:
                    # If move is invalid, reset to original position
                    selected_piece.update_location(orig_pos)
                    selected_piece = None
                    valid_moves = []

    # -----------------------------
    # Drawing Section
    # -----------------------------
    screen.fill((0, 0, 0))       # Clear screen each frame
    draw_board()                 # Draw blue and white board
    draw_all_pieces()            # Draw all checkers

    # Highlight pieces forced to jump (yellow border)
    forced_pieces = get_forced_jump_pieces(current_turn)
    for piece in forced_pieces:
        pygame.draw.circle(screen, HIGHLIGHT_YELLOW, piece.location, piece.radius + 5, 4)

    # Show valid moves for selected piece (small yellow dots)
    if selected_piece:
        for (r, c) in valid_moves:
            pygame.draw.circle(screen, HIGHLIGHT_YELLOW, board_to_pixel(r, c), 12)

    # Green highlight for hovered piece
    if hover_piece and hover_piece not in forced_pieces:
        pygame.draw.circle(screen, HIGHLIGHT_GREEN, hover_piece.location, hover_piece.radius + 5, 3)

    # Red highlight for currently selected piece
    if selected_piece:
        pygame.draw.circle(screen, HIGHLIGHT_RED, selected_piece.location, selected_piece.radius + 5, 3)

    # Display current player's turn at top-left of window
    turn_text = font.render(f"Turn: {'White' if current_turn == WHITE else 'Black'}", True, (0, 0, 0))
    screen.blit(turn_text, (10, 10))

    # Update everything drawn to the window
    pygame.display.flip()

# End the program once the window closes
pygame.quit()
