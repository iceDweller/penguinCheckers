import pygame

# Initialize Pygame
pygame.init()

# Constants
ROWS = 8
TILE_SIZE = 95
WIDTH = HEIGHT = ROWS * TILE_SIZE
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Penguin Checkers")

# Colors
BLUE = (0, 102, 204)
WHITE = (255, 255, 255)
PIECE_BLUE = (0, 0, 255)
PIECE_WHITE = (240, 240, 240)

# Game Loop Control
clock = pygame.time.Clock()
running = True

# Selection State
selected_piece = None  # To keep track of selected piece

# Helper
def is_dark_square(r, c):
    return (r + c) % 2 != 0

# Draw Functions
def draw_board():
    for row in range(ROWS):
        for col in range(ROWS):
            color = WHITE if (row + col) % 2 == 0 else BLUE
            pygame.draw.rect(screen, color,
                             (col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE))

def draw_pieces():
    radius = TILE_SIZE // 2 - 12
    for r in range(ROWS):
        for c in range(ROWS):
            piece = board[r][c]
            if piece in (1, 3):  # Player 1 or king
                color = PIECE_BLUE
            elif piece in (2, 4):  # Player 2 or king
                color = PIECE_WHITE
            else:
                continue

            # Draw main piece
            pygame.draw.circle(
                screen, color,
                (c * TILE_SIZE + TILE_SIZE // 2, r * TILE_SIZE + TILE_SIZE // 2),
                radius
            )

            # Draw king mark
            if piece in (3, 4):
                pygame.draw.circle(
                    screen, (255, 215, 0),  # Gold ring
                    (c * TILE_SIZE + TILE_SIZE // 2, r * TILE_SIZE + TILE_SIZE // 2),
                    radius - 20, 3
                )

    # Draw red border for selected piece
    if selected_piece:
        r, c = selected_piece
        pygame.draw.rect(screen, (255, 0, 0),
                         (c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE), 3)


    # Draw red border around selected piece
    if selected_piece:
        r, c = selected_piece
        pygame.draw.rect(screen, (255, 0, 0), (c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE), 3)

font = pygame.font.Font(None, 40)

def draw_turn():
    text = font.render(f"Player {current_player}'s Turn", True, (255, 0, 0))
    screen.blit(text, (10, HEIGHT - 40))


# Checks if the move is valid
def valid_move(row, col, from_row, from_col):
    if not is_dark_square(row,col):
        return False
    if not board[row][col] == 0: # not empty
        return False
    piece = board[from_row][from_col]

    # Determine movement direction
    if piece in (1, 3):  # Player 1 or king
        direction = 1
    if piece in (2, 4):  # Player 2 or king
        direction = -1


    # Normal pieces move one diagonal step forward
    if abs(col - from_col) == 1 and (
        row == from_row + direction or piece in (3, 4) and row == from_row - direction
    ):
        return True

    # Capture (jump)
    elif abs(col - from_col) == 2 and (
        row == from_row + 2 * direction or piece in (3, 4) and row == from_row - 2 * direction
    ):
        mid_r = (from_row + row) // 2
        mid_c = (from_col + col) // 2
        if board[mid_r][mid_c] not in (0, piece, 3 if piece == 1 else 4):
            return True


    return False

# Create Board
board = [[0 for _ in range(ROWS)] for _ in range(ROWS)]
for r in range(0, 3):
    for c in range(ROWS):
        if is_dark_square(r, c):
            board[r][c] = 1
for r in range(5, 8):
    for c in range(ROWS):
        if is_dark_square(r, c):
            board[r][c] = 2

# Main Game Loop
current_player = 1  # Player 1 (blue) starts
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            row = mouse_y // TILE_SIZE
            col = mouse_x // TILE_SIZE

            if selected_piece is None:
                # Only select the current player's piece
                if board[row][col] == current_player or board[row][col] == current_player + 2:
                    selected_piece = (row, col)

            else:
                from_row, from_col = selected_piece
                if valid_move(row, col, from_row, from_col):
                    piece = board[from_row][from_col]
                    board[row][col] = piece
                    board[from_row][from_col] = 0
                    
                    current_player = 2 if current_player == 1 else 1
                    
                    # Check if it was a capture move (jump)
                    if abs(row - from_row) == 2:
                        mid_r = (from_row + row) // 2
                        mid_c = (from_col + col) // 2
                        board[mid_r][mid_c] = 0  # Remove captured piece

                    

                selected_piece = None
            
            # Check for promotion
            if board[row][col] == 1 and row == ROWS - 1:
                board[row][col] = 3  # Player 1 king
            elif board[row][col] == 2 and row == 0:
                board[row][col] = 4  # Player 2 king


    draw_board()
    draw_pieces()
    draw_turn()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
