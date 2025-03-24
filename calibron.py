#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
@File    :   calibron.py
@Time    :   2025/03/16 23:40:08
@Author  :   Oriol Nieto
@Contact :   onieto@adobe.com
@Desc    :   Calibron-12 solver using a backtracking algorithm

The Calibron-12 puzzle consists of 12 rectangular pieces that must fit perfectly
into a 56x56 square board. This solver implements a backtracking algorithm with
the following steps:

Algorithm Steps:
1. Initialization
   - Create an empty 56x56 board
   - Define 12 pieces with their respective dimensions
   - Verify total area of pieces equals board area

2. Piece Placement Strategy
   - Always place pieces starting from the top-left empty position
   - For each piece attempt:
     a. Try the original orientation
     b. Try the transposed (90-degree rotated) orientation
   - Only place pieces in valid positions (no overlaps, within bounds)

3. Backtracking Process
   - For each empty position:
     a. Try placing each available piece
     b. If placement successful, recursively try to place remaining pieces
     c. If placement fails or no solution found, remove piece and try next option
     d. If all options exhausted, backtrack to previous position

4. Solution Detection
   - Solution is found when all 12 pieces are successfully placed
   - If no valid placement is possible, backtrack and try different configurations

Time Complexity: O(2^n * n!), where n is the number of pieces
Space Complexity: O(n), where n is the number of pieces (due to recursion stack)

Note: This is a naive implementation that explores all possible combinations
until a solution is found or all possibilities are exhausted.
"""

import logging
from copy import deepcopy

import numpy as np

ROWS = 56
COLS = 56
EMPTY_PIECE_ID = 0
PIECE_SHAPES = [
    [28, 6],
    [28, 7],
    [32, 11],
    [32, 10],
    [14, 4],
    [10, 7],
    [17, 14],
    [28, 14],
    [21, 14],
    [21, 18],
    [21, 18],
    [21, 14],
]

# For pretty printing
PRETTY_MAP = {i: str(i) for i in range(len(PIECE_SHAPES))}
PRETTY_MAP[EMPTY_PIECE_ID] = "X"
PRETTY_MAP[10] = "A"
PRETTY_MAP[11] = "B"
PRETTY_MAP[12] = "C"


class Board(object):
    def __init__(self, rows=ROWS, cols=COLS):
        self.rows = rows
        self.cols = cols
        self.board = np.zeros((self.rows, self.cols), dtype=np.int16)
        self.pieces = []

    def draw(self):
        margins = "+" + "-" * self.cols + "+"
        body = []
        for row in self.board:
            body.append("|" + "".join(map(lambda x: PRETTY_MAP[x], row)) + "|")
        print(margins)
        print("\n".join(body))
        print(margins)

    def check_piece(self, piece):
        # Check if piece is already in the board
        return any(p.id == piece.id for p in self.pieces)

    def add_piece(self, piece):
        # If piece is already in the board, we can't add it
        if self.check_piece(piece):
            return False

        # Find top-left corner of the first empty space
        row, col = self.find_top_left_non_empty()
        if row is None:
            # Board is empty, add piece to top left corner
            row, col = 0, 0

        # Check if piece goes out of bounds
        if row + piece.height > self.rows or col + piece.width > self.cols:
            return False

        # Check if piece fits
        if np.any(
            self.board[row : row + piece.height, col : col + piece.width]
            != EMPTY_PIECE_ID
        ):
            return False

        # Piece fits, add it to the board
        self.board[row : row + piece.height, col : col + piece.width] = piece.id
        self.pieces.append(piece)
        return True

    def remove_piece(self, piece):
        # Remove piece from board
        self.board[self.board == piece.id] = EMPTY_PIECE_ID
        self.pieces.remove(piece)

    def count_pieces(self):
        return len(self.pieces)

    def find_top_left_non_empty(self, empty_piece_id=EMPTY_PIECE_ID):
        # Use cumsum to find the first zero element in each row
        cumsum = np.cumsum(self.board == empty_piece_id, axis=1)

        for i in range(self.rows):
            if np.any(self.board[i] == empty_piece_id):
                col = np.argmax(cumsum[i] > 0)
                return i, col

        return None, None


class Piece(object):
    def __init__(self, width, height, id, vertical=False):
        self.id = id
        self.vertical = vertical
        self.width = width
        self.height = height
        if self.vertical:
            self.width = height
            self.height = width
        self.area = self.width * self.height

    def transpose(self):
        self.width, self.height = self.height, self.width
        self.vertical = not self.vertical


def try_piece_placement(board, piece, pieces, pbar=False, transposed=False):
    """Attempt to place a piece on the board and recursively solve.

    Parameters
    ----------
    board : Board
        The game board object where pieces will be placed
    piece : Piece
        The piece to attempt to place
    pieces : list of Piece
        List of all available pieces
    pbar : bool, optional
        If True, logs progress information, by default False
    transposed : bool, optional
        If True, indicates this is a transposed piece attempt, by default False

    Returns
    -------
    bool
        True if placement leads to a solution, False otherwise
    """
    if pbar:
        transposed_mark = "(transposed) " if transposed else ""
        logging.info(
            f"Trying piece {piece.id} {transposed_mark}of {len(PIECE_SHAPES)}..."
        )

    if board.add_piece(piece):
        if fit_board(board, pieces):
            return True
        board.remove_piece(piece)
    return False


def fit_board(board, pieces, pbar=False):
    """Recursively attempt to fit all pieces onto the board.

    This function uses a backtracking algorithm to try placing each piece on the board,
    including rotated versions of the pieces, until either all pieces are placed or
    no solution is found.

    Parameters
    ----------
    board : Board
        The game board object where pieces will be placed
    pieces : list of Piece
        List of all available pieces that need to be placed on the board
    pbar : bool, optional
        If True, logs progress information about piece placement attempts,
        by default False

    Returns
    -------
    bool
        True if a valid solution is found (all pieces placed),
        False if no solution exists

    Notes
    -----
    The function attempts to place each piece in two orientations:
    1. Original orientation
    2. Transposed (rotated 90 degrees)

    If a piece placement is successful, the function recursively tries to place
    the remaining pieces. If at any point the placement fails, it backtracks
    by removing the last placed piece and tries a different configuration.
    """
    if board.count_pieces() == len(PIECE_SHAPES):
        logging.info("Solution found!")
        return True

    for piece in pieces:
        if piece not in board.pieces:
            # Try original orientation
            if try_piece_placement(board, piece, pieces, pbar):
                return True

            # Try rotated orientation
            tpiece = deepcopy(piece)
            tpiece.transpose()
            if try_piece_placement(board, tpiece, pieces, pbar, transposed=True):
                return True

    return False


def sort_pieces(pieces):
    """Sort pieces by area (largest first) and perimeter to prioritize placement.

    Larger pieces are harder to place, so placing them first reduces backtracking.
    """
    return sorted(pieces, key=lambda p: (-p.area, -(p.width + p.height)))


def main():
    # Create board
    board = Board()

    # Create pieces
    pieces = []
    for i, (width, height) in enumerate(PIECE_SHAPES):
        piece = Piece(width, height, id=i + 1, vertical=False)
        pieces.append(piece)
        logging.info(f"Piece {PRETTY_MAP[piece.id]}: {piece.width}x{piece.height}")

    # Sanity check
    assert sum([piece.area for piece in pieces]) == board.rows * board.cols, (
        "Pieces do not fit in the board"
    )

    # Fit board
    fit_board(board, pieces, pbar=True)

    # Print solution
    board.draw()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
