import pygame

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock=pygame.time.Clock()
running=True
player_pos = pygame.mouse.get_pos()
dt = 0
pygame.image.load("42c2518e-997c-49ce-8c7d-4ef6c8eba1a6.png")
pygame.display.update()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running=False
    x,y= 0,0
    while x< 7:
        while y<7:
            pygame.draw.rect(screen,"green",(x,y*100,100,100))
            y+1
        x+1
    player_pos = pygame.mouse.get_pos()
    pygame.draw.circle(screen, "red", player_pos, 10, 0)
    pygame.display.flip()
    dt = clock.tick(60) / 1000
    r = pygame.Rect(10,10,100,100)
    pygame.draw.rect(screen, "green", r)
    pygame.display.update()




print("hello world")


rows, columns = 8,8
board = [[0]*rows]*columns
print(board)