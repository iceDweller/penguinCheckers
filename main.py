import pygame

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock=pygame.time.Clock()
running=True
player_pos = pygame.mouse.get_pos()
dt = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running=False
    screen.fill((0, 0, 0))
    player_pos = pygame.mouse.get_pos()
    pygame.draw.circle(screen, "red", player_pos, 10, 0)
    pygame.display.flip()
    dt = clock.tick(60) / 1000



print("hello world")


rows, columns = 8,8
board = [[0]*rows]*columns
print(board)
#6tf7f7f7yf