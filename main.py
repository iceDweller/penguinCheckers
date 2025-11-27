import pygame
import time
import random
# Initialize Pygame so we can use all its built-in graphics functions
pygame.init()

# -----------------------------
# Window / Board Setup
# -----------------------------
# create an 800x800 window initially with scalability
UI_SPACE_HEIGHT = 60
info = pygame.display.Info()
SCREEN_WIDTH = min(info.current_w-100,800)
SCREEN_HEIGHT = min(info.current_h-100,800)+60
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE) #add pygame.RESIZABLE if you want to mess with scaling (I do not right now)
pygame.display.set_caption("Penguin Checkers")


# Options for AI difficulty
AI_DIFFICULTY = "HARD"  #"EASY" or "HARD"

UI_SCALE = 1.0
MENU_SCALE = 1.0


# calc tile size based on screen
TILE_SIZE = min(SCREEN_WIDTH,SCREEN_HEIGHT)//8
BOARD_SIZE = TILE_SIZE*8
BOARD_OFFSET_X = (SCREEN_WIDTH-BOARD_SIZE)//2
BOARD_OFFSET_Y = 0
ROWS = 8

# Define board colors (light and dark squares)
BLUE_TILE = (0, 102, 204)     # Dark squares (blue)
WHITE_TILE = (255, 255, 255)  # Light squares (white)

# Define piece colors
BLACK = (35, 35, 35)             # Black player pieces
BLACK_BORDER = (70,70,70)
WHITE = (255, 255, 255)       # White player pieces
WHITE_BORDER = (200,200,200)
HIGHLIGHT_WIDTH = 5

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

# -----------------------------
# Checker Class - represents one checker piece
# -----------------------------
class Checker:
    def __init__(self, location, status, player):
        self.location = location   # Current pixel position of the piece
        self.status = status       # "normal" or "king"
        self.player = player       # Which player this piece belongs to
        self.king = False          # Whether the piece is a king yet
        self.radius = TILE_SIZE//3           # Circle size for the piece
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
        if self.player == WHITE:
            pygame.draw.circle(screen, WHITE_BORDER, self.location, self.radius, HIGHLIGHT_WIDTH)
        else:
            pygame.draw.circle(screen, BLACK_BORDER, self.location, self.radius, HIGHLIGHT_WIDTH)
        if self.king:
            pygame.draw.circle(screen, HIGHLIGHT_GOLD, self.location, self.radius // 2)

    def clicked(self, mouse_pos):
        """Return True if the mouse clicked on this piece."""
        return self.rect.collidepoint(mouse_pos)


class easy_AI:
    def __init__(self,color):
        self.color = color

    def pick_move(self):
        moves = get_all_player_moves(self.color)

        if not moves:
            return None



        piece, (r,c) = random.choice(moves)
        return piece, (r,c)



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

            x,y = board_to_pixel(r,c)

            # Black pieces occupy the top 3 rows
            if r < 3:
                board_state.append(Checker((x, y), "normal", BLACK))
            # White pieces occupy the bottom 3 rows
            elif r > 4:
                board_state.append(Checker((x, y), "normal", WHITE))

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
    pieces = [p for p in board_state if p.player == player_color]
    jump_pieces = []
    for piece in pieces:
        # Check if this piece has any jump moves available
        jump_moves = get_valid_moves(piece, only_jumps=True)
        if jump_moves:  # If there are any jump moves, this piece must jump
            jump_pieces.append(piece)
    return jump_pieces

def reset_game():
    global board_state, turn, selected_piece, valid_moves, dragging
    global orig_pos,multi_jump,jump_occurred,hover_piece,game_over,game_winner,board_history
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

def check_game_over():
    global game_over, game_winner

    #get num pieces for each player
    white_pieces = [p for p in board_state if p.player==WHITE]
    black_pieces = [p for p in board_state if p.player==BLACK]

    if len(white_pieces) == 0:
        game_over = True
        game_winner = "BLACK"
        return True
    if len(black_pieces) == 0:
        game_over = True
        game_winner = "WHITE"
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

def draw_menu():
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

    btn_w = int(30 * MENU_SCALE)
    btn_h = int(30 * MENU_SCALE)
    btn_x = int(menu_x + menu_width - (40 * MENU_SCALE))
    btn_y = int(menu_y + 10 * MENU_SCALE)

    close_button = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
    pygame.draw.rect(screen, (255, 0, 0), close_button)

    close_text = menu_font.render("X", True, (255, 255, 255))
    screen.blit(close_text, (close_button.centerx - close_text.get_width() // 2,
                             close_button.centery - close_text.get_height() // 2))

    return close_button

def draw_ui_buttons():
    # Draw UI bar background
    pygame.draw.rect(screen, (50, 50, 50), (0, 0, SCREEN_WIDTH, UI_SPACE_HEIGHT))
    pygame.draw.rect(screen, (100, 100, 100), (0, 0, SCREEN_WIDTH, UI_SPACE_HEIGHT), 4)

    font_size = int(36 * UI_SCALE)
    ui_font = pygame.font.SysFont(None, font_size)

    # Draw turn indicator
    turn_text = ui_font.render(f"Turn: {'White' if turn % 2 == 0 else 'Black'}", True, (255, 255, 255))
    screen.blit(turn_text, (10 * UI_SCALE, 10 * UI_SCALE))

    # Menu button
    button_w = int(100 * UI_SCALE)
    button_h = int(40 * UI_SCALE)
    padding = int(10 * UI_SCALE)
    menu_button = pygame.Rect(SCREEN_WIDTH - (button_w * 2 + padding * 2), padding, button_w, button_h)
    reset_button = pygame.Rect(SCREEN_WIDTH - (button_w + padding), padding, button_w, button_h)

    # Menu button visuals
    pygame.draw.rect(screen, (50, 50, 150), menu_button)
    pygame.draw.rect(screen, (100, 100, 200), menu_button, 2)
    menu_text = ui_font.render("Menu", True, (255, 255, 255))
    screen.blit(menu_text, (menu_button.centerx - menu_text.get_width() // 2, menu_button.centery - menu_text.get_height() // 2))

    # Reset button visuals
    pygame.draw.rect(screen, (150, 50, 50), reset_button)
    pygame.draw.rect(screen, (200, 100, 100), reset_button, 2)
    reset_text = ui_font.render("Reset", True, (255, 255, 255))
    screen.blit(reset_text, (reset_button.centerx - reset_text.get_width() // 2, reset_button.centery - reset_text.get_height() // 2))

    return menu_button, reset_button


def scale_window(new_size):
    global SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, BOARD_SIZE, BOARD_OFFSET_X, BOARD_OFFSET_Y
    global screen, board_state, UI_SPACE_HEIGHT, UI_SCALE, MENU_SCALE

    # Save old board info before resizing
    old_tile = TILE_SIZE
    old_offset_x = BOARD_OFFSET_X
    old_ui_height =UI_SPACE_HEIGHT

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
    


    #redraq immediately
    pygame.display.flip()



def save_game_state():
    print()

# add anything here you want to call whenever a turn ends (i.e. print debugging)
def on_turn_end():
    check_game_over()
    save_game_state()
    # print(board_state)

def logic_board():
    board = [[None for _ in range(8)] for _ in range(8)]
    for p in board_state:
        r,c = pixel_to_board(p.location)
        if p.king:
            board[r][c]=("Wk" if p.player == WHITE else "Bk")
        else:
            board[r][c] = ("W" if p.player == WHITE else "B")


def get_all_player_moves(player_color):
    moves =[]
    forced = get_forced_jump_pieces(player_color)

    pieces = forced if forced else [p for p in board_state if p.player == player_color]
    for p in pieces:
        valid = get_valid_moves(p,only_jumps=bool(forced))
        for(r,c) in valid:
            moves.append((p,(r,c)))
    return moves

def apply_ai_move(ai):
    global turn,selected_piece,valid_moves,jump_occurred,multi_jump
    result =ai.pick_move()
    if not result:
        return
    piece, (r,c) = result

    sr, sc =pixel_to_board(piece.location)
    dr, dc = r-sr,c-sc


    if abs(dr) ==2:
        jumped = piece_at(sr+dr//2,sc+dc//2)
        if jumped:
            board_state.remove(jumped)

    piece.update_location(board_to_pixel(r,c))
    sr2, sc2 =pixel_to_board(piece.location)
    turn +=1
    on_turn_end()

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

        # resize window (EXPERIMENTAL)
        if event.type == pygame.VIDEORESIZE:
            scale_window(event.size)

        if not show_menu:
            # Hover highlight (shows green outline when cursor hovers over a piece)
            if event.type == pygame.MOUSEMOTION:
                hover_piece = None
                adj_mpos = (mouse_pos[0], mouse_pos[1])  # Adjust mouse position
                for piece in board_state:
                    if piece.rect.collidepoint(adj_mpos):  # Use adjusted position for hover
                        hover_piece = piece
                        break

            # Pick up a piece (left click)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Check if UI buttons were clicked
                menu_button, reset_button = draw_ui_buttons()  # Draw UI and get button positions

                if menu_button.collidepoint(mouse_pos):
                    show_menu = True
                elif reset_button.collidepoint(mouse_pos):
                    reset_game()
                elif not selected_piece and not game_over:
                    for piece in board_state:
                        # Only allow clicking on your own turn's pieces
                        if piece.clicked(mouse_pos) and piece.player == get_current_turn():
                            forced_pieces = get_forced_jump_pieces(get_current_turn())
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
                                offset_x = 0
                                offset_y = 0
                                break

            # Drag piece with mouse
            if event.type == pygame.MOUSEMOTION and dragging and selected_piece:
                mx, my = mouse_pos
                selected_piece.update_location((mx, my))

            # Drop piece (when releasing mouse)
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and dragging:
                dragging = False
                if selected_piece:
                    row, col = pixel_to_board(mouse_pos)

                    sr, sc = pixel_to_board(orig_pos)
                    dr, dc = row - sr, col - sc

                    # Check if move is valid
                    if (row, col) in valid_moves:
                        # Handle jump moves
                        if abs(dr) == 2:
                            jumped = piece_at(sr + dr // 2, sc + dc // 2)
                            if jumped:
                                board_state.remove(jumped)
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
                                turn += 1
                                on_turn_end()
                        else:
                            # Normal (non-jump) move
                            if jump_occurred:
                                selected_piece.update_location(orig_pos)
                            else:
                                selected_piece.update_location(board_to_pixel(row, col))
                                selected_piece = None
                                valid_moves = []
                                turn += 1
                                on_turn_end()
                    else:
                        # If move is invalid, reset to original position
                        selected_piece.update_location(orig_pos)
                        selected_piece = None
                        valid_moves = []
        if not dragging and not game_over:
            if turn % 2 == 1:  # Black's turn (AI)
                if AI_DIFFICULTY == "EASY":
                    ai = easy_AI(BLACK)
                else:
                    ai = hard_AI(BLACK)
                apply_ai_move(ai)


        # Handle menu events
        else:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                close_button = draw_menu()
                if close_button.collidepoint(mouse_pos):
                    show_menu = False

    # -----------------------------
    # Drawing Section
    # -----------------------------
    screen.fill((0, 0, 0))       # Clear screen each frame
    if not show_menu:
        draw_ui_buttons()
        draw_board()  # Draw blue and white board
        draw_all_pieces()  # Draw all checkers

        # Highlight pieces forced to jump (yellow border)
        forced_pieces = get_forced_jump_pieces(get_current_turn())
        for piece in forced_pieces:
            screen_pos = (piece.location[0], piece.location[1])
            pygame.draw.circle(screen, HIGHLIGHT_YELLOW, screen_pos, piece.radius + 5, 4)

        # Show valid moves for selected piece (small yellow dots)
        if selected_piece:
            for (r, c) in valid_moves:
                screen_pos = board_to_screen_pixel(r, c)  # Use screen coordinates with UI offset
                pygame.draw.circle(screen, HIGHLIGHT_YELLOW, screen_pos, TILE_SIZE // 6)

        # Green highlight for hovered piece
        if hover_piece and hover_piece not in forced_pieces:
            screen_pos = (hover_piece.location[0], hover_piece.location[1])
            pygame.draw.circle(screen, HIGHLIGHT_GREEN, screen_pos, hover_piece.radius + 5, 3)

        # Red highlight for currently selected piece
        if selected_piece:
            screen_pos = (selected_piece.location[0], selected_piece.location[1])  # Remove + UI_SPACE_HEIGHT
            pygame.draw.circle(screen, HIGHLIGHT_RED, screen_pos, selected_piece.radius + 5, 3)

        if game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            game_over_text = font.render(f"Game over, {game_winner} wins!", True, (255, 255, 255))
            screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2,SCREEN_HEIGHT // 2 - game_over_text.get_height() // 2))
    else:
        close_button=draw_menu()



    # Update everything drawn to the window
    pygame.display.flip()



# End the program once the window closes
pygame.quit()
