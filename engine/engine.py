import random


class ChessEngine:
    """The artificial system that calculates the next move for the current game state."""

    def next_move(self, board):
        return random.choice(list(board.legal_moves))
