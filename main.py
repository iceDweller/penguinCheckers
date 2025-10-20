import pygame

# Initialize Pygame
pygame.init()
# Board Settings
# Number of rows and columns (8x8 for checkers)
ROWS = 8
# Each square tile is 100px
TILE_SIZE = 100
# Total window size (800 x 800)
WIDTH = HEIGHT = ROWS * TILE_SIZE
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Penguin Checkers")
# My colors for the board
# Dark tile color
BLUE = (0, 102, 204)
# Light tile color
WHITE = (255, 255, 255)
# Piece colors (circles); pieces only sit on dark tiles
PIECE_BLUE  = (0, 0, 255)
PIECE_WHITE = (240, 240, 240)
# Game Loop Control
clock = pygame.time.Clock()
running = True
# helpers
def is_dark_square(r, c):
    return (r + c) % 2 != 0
# Draws the 8x8 Checkerboard
def draw_board():
    """
    Draws an 8x8 checkerboard on the screen.
    Alternates between blue and white tiles based on row + column parity.
    """
    for row in range(ROWS):
        for col in range(ROWS):
            # Choose color: white if even, blue if odd
            color = WHITE if (row + col) % 2 == 0 else BLUE
            # Draw each square tile
            pygame.draw.rect(screen, color,
                             (col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE))
def draw_pieces():
    """Draw all pieces based on the board array."""
    # a little smaller than the square
    radius = TILE_SIZE // 2 - 12
    for r in range(ROWS):
        for c in range(ROWS):
            piece = board[r][c]
            # Draw blue pieces
            if piece == 1:
                pygame.draw.circle(
                    screen, PIECE_BLUE,
                    # Calculate the center of the current square
                    (c * TILE_SIZE + TILE_SIZE // 2, r * TILE_SIZE + TILE_SIZE // 2),
                    radius
                )
            # Draw white pieces
            elif piece == 2:
                pygame.draw.circle(
                    screen, PIECE_WHITE,
                    # Calculate the center of the current square
                    (c * TILE_SIZE + TILE_SIZE // 2, r * TILE_SIZE + TILE_SIZE // 2),
                    radius
                )
# Create a 2D list (8x8) initialized to 0 to represent empty squares
board = [[0 for _ in range(ROWS)] for _ in range(ROWS)]
# Debug print to verify board structure in the console
print(board)
# Top three rows: BLUE pieces on dark squares
for r in range(0, 3):
    for c in range(ROWS):
        if is_dark_square(r, c):
            board[r][c] = 1
# Bottom three rows: WHITE pieces on dark squares
for r in range(5, 8):
    for c in range(ROWS):
        if is_dark_square(r, c):
            board[r][c] = 2
# Main Game Loop
while running:
    # Handle events (close window, etc.)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    # Draw the board every frame
    draw_board()
    #put pieces in default position
    draw_pieces()
    # Update the display
    pygame.display.flip()
    # Control the frame rate
    clock.tick(60)
# Clean up when the game window is closed
pygame.quit()

