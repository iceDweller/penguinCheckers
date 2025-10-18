'''    import pygame

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







    rows, columns = 8,8
    board = [[0]*rows]*columns
    print(board)
'''
import pygame

pygame.init()

screen = pygame.display.set_mode((1280, 1280))

#background = pygame.image.load("42c2518e-997c-49ce-8c7d-4ef6c8eba1a6.png").convert()

#screen.blit(background, (0, 0))

clock = pygame.time.Clock()

pygame.display.flip()

running = True
class checker:

    def __init__(self,location,status,player):
        self.location = location
        self.status = status
        self.player = player
        pygame.draw.circle(screen,player,location, 20)
    def update_location(self,new_location):
        self.location = new_location
    def draw_self(self):
        pygame.draw.circle(screen,self.player,self.location,20)


def checker_creation():
    i=0

    x = 0
    while i < 2:
        if i == 0:
            x = 0
            while x < 12:
                player_blue_list_of_checkers.append(checker((640, 0), "normal", "blue"))
                x = x + 1
        elif i == 1:
            x = 0
            while x < 12:
                player_red_list_of_checkers.append(checker((640, 640), "normal", "red"))
                x = x + 1
        i = i + 1
def board_creation():
    i = 0
    while i<8:
        x=0
        if i%2== 0:
            while x < 8:
                if x%2 == 1:
                    pygame.draw.rect(screen, "red",(x*8*10,i*8*10,80,80))

                else:
                    pygame.draw.rect(screen, "blue", (x * 8 * 10, i * 8 * 10,80,80))
                    #if i <4: player_blue_list_of_checkers.append(checker(((x * 8 * 10)-40,(i * 8 * 10)-40),"normal" ,"red"))
                x = x + 1
        else:
            while x < 8:
                if x % 2 == 1:
                    pygame.draw.rect(screen, "blue", (x * 8 * 10, i * 8 * 10, 80, 80))
                    #if i<4: player_blue_list_of_checkers.append(checker(((x * 8 * 10) - 40, (i * 8 * 10) - 40), "normal", "red"))
                else:
                    pygame.draw.rect(screen, "red", (x * 8 * 10, i * 8 * 10, 80, 80))
                x = x + 1
        i = i + 1
        pygame.display.flip()

def screen_update():
    for i in range(len(player_blue_list_of_checkers)):

def startup():

    player_white_list_of_checkers=[]
    player_black_list_of_checkers= []
    players_checkers =[player_white_list_of_checkers,player_black_list_of_checkers]
    for i in range(len(players_checkers)):
        for x in range(len(players_checkers[i])):
            players_checkers[i][x].append(checker((0,0),"normal",i))
    print(player_black_list_of_checkers)
#startup()
player_blue_list_of_checkers =[]
player_red_list_of_checkers = []
checker_creation()
board_creation()
print(range(len(player_blue_list_of_checkers)))
while running:

    clock.tick(60)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False

    player_pos = pygame.mouse.get_pos()





