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
# My colors for the borad
# Dark tile color
BLUE = (0, 102, 204)
# Light tile color
WHITE = (255, 255, 255)
# Game Loop Control
clock = pygame.time.Clock()
running = True
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
# Create a 2D list (8x8) initialized to 0 to represent empty squares
board = [[0 for _ in range(ROWS)] for _ in range(ROWS)]
# Debug print to verify board structure in the console
print(board)

# Main Game Loop
while running:
    # Handle events (close window, etc.)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    # Draw the board every frame
    draw_board()
    # Update the display
    pygame.display.flip()
    # Control the frame rate
    clock.tick(60)
# Clean up when the game window is closed
pygame.quit()
