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
    col,row = 8,8
    x,y = 0,0
    while y < col*100:
        while x < row*100:
            pygame.draw.rect(screen, "blue", (x,y,100,100), 0)
            pygame.draw.rect(screen, "green", (x+100,y,100,100), 0) 
            x+=100
        y+=100
            

    #pygame.draw.rect(screen, "green", (0,0,100,100), 0)
    #pygame.draw.rect(screen, "blue", (100,0,100,100), 0)
    #pygame.draw.rect(screen, "green", (200,0,100,100), 0)
    #pygame.draw.rect(screen, "blue", (0,100,100,100), 0)
    #pygame.draw.rect(screen, "green", (100,100,100,100), 0)
    #pygame.draw.rect(screen, "blue", (200,200,100,100), 0)

    pygame.draw.circle(screen, "red", player_pos, 10, 0)
    pygame.display.flip()
    dt = clock.tick(60) / 1000



print("hello world")


rows, columns = 8,8
board = [[0]*rows]*columns
print(board)