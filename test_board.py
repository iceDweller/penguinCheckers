# This file contains automated unit tests for verifying
# the initial setup of the Penguin Checkers game board.
# It checks board dimensions, dark tile placement, and
# piece placement logic.

# Python's built-in unit testing framework
import unittest

ROWS = 8
# Helper Functions
def is_dark_square(r, c):
    return (r + c) % 2 != 0

def make_starting_board():
    # Initialize an 8x8 board with zeros (empty spaces)
    board = [[0 for _ in range(ROWS)] for _ in range(ROWS)]
    # Place blue pieces on top 3 rows (only on dark squares)
    for r in range(0, 3):
        for c in range(ROWS):
            if is_dark_square(r, c): board[r][c] = 1
    # Place white pieces on bottom 3 rows (only on dark squares)
    for r in range(5, 8):
        for c in range(ROWS):
            if is_dark_square(r, c): board[r][c] = 2
    return board

# Each method inside this class tests one aspect of the board setup.
# The unittest framework will automatically find and run these tests.
class TestBoard(unittest.TestCase):
    def test_board_dimensions(self):
        #Checks that the board has the correct number of rows (8).
        # This ensures the game grid size matches standard checkers
        self.assertEqual(ROWS, 8)

    def test_is_dark_square_pattern(self):
        darks = sum(1 for r in range(8) for c in range(8) if is_dark_square(r,c))
        #Counts how many dark squares there are on the board.
        # A regular checkers board should have 32 dark tiles.
        self.assertEqual(darks, 32)

    def test_starting_positions_counts(self):
        #Verifies that there are exactly 12 blue and 12 white pieces
        # placed on the board at the start of the game.
        # This matches standard checkers rules
        b = make_starting_board()
        blue = sum(1 for r in range(8) for c in range(8) if b[r][c] == 1)
        white = sum(1 for r in range(8) for c in range(8) if b[r][c] == 2)
        self.assertEqual((blue, white), (12, 12))

    def test_piece_on_dark_only(self):
        #Ensures that all pieces are placed only on dark tiles
        # and not on light tiles. This is a core rule of checkers.\
        b = make_starting_board()
        for r in range(8):
            for c in range(8):
                # If there's a piece at this position
                if b[r][c] != 0:
                    self.assertTrue(is_dark_square(r,c))
# Test Runner
if __name__ == "__main__":
    unittest.main()
