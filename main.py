import pygame

# Initialize Pygame
pygame.init()

# Constants
ROWS = 8
TILE_SIZE = 75
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
            if piece == 1:
                pygame.draw.circle(
                    screen, PIECE_BLUE,
                    (c * TILE_SIZE + TILE_SIZE // 2, r * TILE_SIZE + TILE_SIZE // 2),
                    radius
                )
            elif piece == 2:
                pygame.draw.circle(
                    screen, PIECE_WHITE,
                    (c * TILE_SIZE + TILE_SIZE // 2, r * TILE_SIZE + TILE_SIZE // 2),
                    radius
                )

    # Draw red border around selected piece
    if selected_piece:
        r, c = selected_piece
        pygame.draw.rect(screen, (255, 0, 0), (c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE), 3)

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
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            row = mouse_y // TILE_SIZE
            col = mouse_x // TILE_SIZE

            if selected_piece == None:
                # select a piece
                if board[row][col] != 0:
                    selected_piece = (row,col)
            else:
                from_row, from_col = selected_piece
                if board[row][col] == 0 and is_dark_square(row, col):
                    board[row][col] = board[from_row][from_col]
                    board[from_row][from_col] = 0
                selected_piece = None


    draw_board()
    draw_pieces()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
