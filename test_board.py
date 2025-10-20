# test_board.py
import unittest

ROWS = 8

def is_dark_square(r, c):
    return (r + c) % 2 != 0

def make_starting_board():
    board = [[0 for _ in range(ROWS)] for _ in range(ROWS)]
    for r in range(0, 3):
        for c in range(ROWS):
            if is_dark_square(r, c): board[r][c] = 1
    for r in range(5, 8):
        for c in range(ROWS):
            if is_dark_square(r, c): board[r][c] = 2
    return board

class TestBoard(unittest.TestCase):
    def test_board_dimensions(self):
        self.assertEqual(ROWS, 8)

    def test_is_dark_square_pattern(self):
        darks = sum(1 for r in range(8) for c in range(8) if is_dark_square(r,c))
        self.assertEqual(darks, 32)

    def test_starting_positions_counts(self):
        b = make_starting_board()
        blue = sum(1 for r in range(8) for c in range(8) if b[r][c] == 1)
        white = sum(1 for r in range(8) for c in range(8) if b[r][c] == 2)
        self.assertEqual((blue, white), (12, 12))

    def test_piece_on_dark_only(self):
        b = make_starting_board()
        for r in range(8):
            for c in range(8):
                if b[r][c] != 0:
                    self.assertTrue(is_dark_square(r,c))

if __name__ == "__main__":
    unittest.main()
