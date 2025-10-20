import pygame

pygame.init()
screen = pygame.display.set_mode((600, 600))
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
    col,row = 8,8
    x,y = 0,0
    while x < row:
        while y < col:
            if (x+y) % 2 == 0:
                pygame.draw.rect(screen, "#dbc8a4", (x*75,y*75,75,75), 0)
            else:
                pygame.draw.rect(screen, "#1c111c", (x*75,y*75,75,75), 0)

            y+=1
        x+=1
        y=0
    if event.type == pygame.MOUSEBUTTONDOWN:
        pygame.draw.circle(screen, "red", player_pos, 10, 0)            
    pygame.display.flip()
    dt = clock.tick(60) / 1000