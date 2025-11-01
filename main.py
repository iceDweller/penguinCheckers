import pygame

# Initialize Pygame
pygame.init()

screen = pygame.display.set_mode((800, 800))
ROWS = 8
TILE_SIZE = 100
BLUE_TILE = (0, 102, 204)
WHITE_TILE = (255, 255, 255)
RED = "red"
BLUE = "blue"
clock = pygame.time.Clock()

player_blue_list_of_checkers = []
player_red_list_of_checkers = []
current_turn = BLUE # BLUE goes first
selected_piece = None
valid_moves = []
dragging = False
orig_pos = None
offset_x = offset_y = 0
multi_jump = False

class checker:
    def __init__(self, location, status, player):
        self.location = location
        self.status = status          # "normal" or "king"
        self.player = player          # color string
        self.king = False
        self.radius = 35
        self.direction = 1 if player == BLUE else -1
        self.update_rect()            # initialize rect

    def update_location(self, new_location):
        self.location = new_location
        self.update_rect()
        # King promotion
        r, _ = pixel_to_board(new_location)
        if not self.king:
            if self.player == BLUE and r == ROWS-1:
                self.make_king()
            elif self.player == RED and r == 0:
                self.make_king()

    def update_rect(self):
        # Keep rect centered on piece
        self.rect = pygame.Rect(
            self.location[0] - self.radius,
            self.location[1] - self.radius,
            self.radius*2,
            self.radius*2
        )

    def make_king(self):
        self.king = True
        self.direction = 0
        self.status = "king"

    def draw_self(self):
        pygame.draw.circle(screen, self.player, self.location, self.radius)
        if self.king:
            pygame.draw.circle(screen, (255, 215, 0), self.location, self.radius//2)

    def clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)


def is_dark_square(r, c):
    return (r + c) % 2 != 0

def create_starting_checkers():
    player_blue_list_of_checkers.clear()
    player_red_list_of_checkers.clear()

    for r in range(ROWS):
        for c in range(ROWS):

            if not is_dark_square(r, c):
                continue

            x = c * TILE_SIZE + TILE_SIZE // 2
            y = r * TILE_SIZE + TILE_SIZE // 2

            if r < 3:
                player_blue_list_of_checkers.append(checker((x, y), "normal", BLUE))
            elif r > 4:
                player_red_list_of_checkers.append(checker((x, y), "normal", RED))

def draw_all_checkers():
    for piece in player_blue_list_of_checkers + player_red_list_of_checkers:
        piece.draw_self()

def draw_board():
    for row in range(ROWS):
        for col in range(ROWS):
            color = WHITE_TILE if (row + col) % 2 == 0 else BLUE_TILE
            pygame.draw.rect(screen, color, (col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE))

create_starting_checkers()
running = True

def pixel_to_board(pos):
    x, y = pos
    return y // TILE_SIZE, x // TILE_SIZE  # row, col

def board_to_pixel(row, col):
    return (col * TILE_SIZE + TILE_SIZE // 2, row * TILE_SIZE + TILE_SIZE // 2)

def piece_at(row, col):
    for p in player_blue_list_of_checkers + player_red_list_of_checkers:
        pr, pc = pixel_to_board(p.location)
        if pr == row and pc == col:
            return p
    return None

def is_dark_square(row, col):
    return (row + col) % 2 != 0

def any_forced_jumps(player_color):
    for piece in (player_blue_list_of_checkers if player_color==BLUE else player_red_list_of_checkers):
        if get_valid_moves(piece, only_jumps=True):
            return True
    return False

def get_valid_moves(piece, only_jumps=False):
    moves = []
    r, c = pixel_to_board(piece.location)

    # King moves all 4 diagonals
    if piece.king:
        directions = [(-1,-1), (-1,1), (1,-1), (1,1)]
    else:
        directions = [(piece.direction,-1), (piece.direction,1)]

    jumps = []

    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < ROWS and 0 <= nc < ROWS and is_dark_square(nr, nc):
            target = piece_at(nr, nc)
            # Normal move
            if not target and not only_jumps:
                moves.append((nr, nc))

            # Jump
            jr, jc = r + dr*2, c + dc*2
            if 0 <= jr < ROWS and 0 <= jc < ROWS and is_dark_square(jr, jc):
                jumped = piece_at(nr, nc)
                if jumped and jumped.player != piece.player and not piece_at(jr, jc):
                    jumps.append((jr, jc))

    # If only jumps exist, return only jumps
    return jumps if jumps else moves

# Initialize helper variables
selected_piece = None
valid_moves = []
dragging = False
orig_pos = None
offset_x = offset_y = 0
current_turn = BLUE
hover_piece = None
multi_jump = False
jump_occurred = False

# Helper to get all pieces that must jump
def get_forced_jump_pieces(player_color):
    pieces = player_blue_list_of_checkers if player_color == BLUE else player_red_list_of_checkers
    forced = []
    for piece in pieces:
        if get_valid_moves(piece, only_jumps=True):
            forced.append(piece)
    return forced

# Main game loop
while running:
    clock.tick(60)
    mouse_pos = pygame.mouse.get_pos()
    row, col = pixel_to_board(mouse_pos)

    # ───────────────
    # Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Hover detection
        if event.type == pygame.MOUSEMOTION:
            hover_piece = None
            for piece in player_blue_list_of_checkers + player_red_list_of_checkers:
                if piece.clicked(mouse_pos):
                    hover_piece = piece
                    break

        # Mouse down — pick up a piece
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not selected_piece:
                for piece in player_blue_list_of_checkers + player_red_list_of_checkers:
                    if piece.clicked(mouse_pos) and piece.player == current_turn:
                        forced_pieces = get_forced_jump_pieces(current_turn)
                        if forced_pieces and piece not in forced_pieces:
                            continue  # cannot select non-forced piece

                        # Only allow jumps if a jump is required or already occurred
                        only_jumps = bool(forced_pieces) or jump_occurred
                        moves = get_valid_moves(piece, only_jumps=only_jumps)
                        if moves:
                            selected_piece = piece
                            valid_moves = moves
                            dragging = True
                            orig_pos = piece.location
                            offset_x = piece.location[0] - mouse_pos[0]
                            offset_y = piece.location[1] - mouse_pos[1]
                            break

        # Dragging
        if event.type == pygame.MOUSEMOTION and dragging and selected_piece:
            mx, my = mouse_pos
            selected_piece.update_location((mx + offset_x, my + offset_y))

        # Mouse up — drop checker
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and dragging:
            dragging = False
            if selected_piece:
                sr, sc = pixel_to_board(orig_pos)
                dr, dc = row - sr, col - sc

                if (row, col) in valid_moves:
                    # Jump move
                    if abs(dr) == 2:
                        jumped = piece_at(sr + dr // 2, sc + dc // 2)
                        if jumped:
                            if jumped in player_blue_list_of_checkers:
                                player_blue_list_of_checkers.remove(jumped)
                            else:
                                player_red_list_of_checkers.remove(jumped)

                        selected_piece.update_location(board_to_pixel(row, col))
                        jump_occurred = True

                        # Check for multi-jump
                        multi_jump = get_valid_moves(selected_piece, only_jumps=True)
                        if multi_jump:
                            valid_moves = multi_jump
                            orig_pos = selected_piece.location
                            dragging = True
                        else:
                            # End turn after last jump
                            selected_piece = None
                            valid_moves = []
                            multi_jump = False
                            jump_occurred = False
                            current_turn = RED if current_turn == BLUE else BLUE

                    else:
                        # Normal move
                        if jump_occurred:
                            # ❌ Cannot make normal move after a jump
                            selected_piece.update_location(orig_pos)
                        else:
                            selected_piece.update_location(board_to_pixel(row, col))
                            selected_piece = None
                            valid_moves = []
                            current_turn = RED if current_turn == BLUE else BLUE
                else:
                    # Illegal drop → snap back
                    selected_piece.update_location(orig_pos)
                    selected_piece = None
                    valid_moves = []

    # ───────────────
    # Drawing
    screen.fill((0,0,0))
    draw_board()
    draw_all_checkers()

    # Highlight forced-jump pieces (thick yellow outline)
    forced_pieces = get_forced_jump_pieces(current_turn)
    for piece in forced_pieces:
        pygame.draw.circle(screen, (255, 255, 0), piece.location, piece.radius+5, 4)

    # Highlight legal moves for selected piece (small yellow circles)
    if selected_piece:
        for (r, c) in valid_moves:
            pygame.draw.circle(screen, (255, 255, 0), board_to_pixel(r, c), 12)

    # Highlight hovered piece (green)
    if hover_piece and hover_piece not in forced_pieces:
        pygame.draw.circle(screen, (0, 255, 0), hover_piece.location, hover_piece.radius+5, 3)

    # Highlight selected piece (red)
    if selected_piece:
        pygame.draw.circle(screen, (255, 0, 0), selected_piece.location, selected_piece.radius+5, 3)

    pygame.display.flip()


