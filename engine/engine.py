import chess
import chess.polyglot
import click
import random
from pathlib import Path


class ChessEngine:
    """The artificial system that calculates the next move for the current game state."""

    def __init__(self, side: chess.Color):
        """Initialize the playing side and the opening book."""
        self.side = chess.WHITE if side == "White" else chess.BLACK
        try:
            ob_file = Path(__file__).parent / "openings.bin"  # Insert name of opening book here
            self.opening_book = chess.polyglot.open_reader(ob_file)
        except:
            click.echo("No opening book was found.")
            self.opening_book = None

    def next_move(self, board: chess.Board) -> str:
        """Find next move to be played by the engine.

        :param board: Current state of board
        :returns: SAN of the move to be played
        """
        # All the currently legal moves
        uci_moves = list(board.legal_moves)
        san_moves = [board.san(move) for move in uci_moves]

        # Play a move from the opening book if book suggests one
        if self.opening_book:
            opening_moves = self.check_opening_sequence(board)
            if opening_moves:
                # Choice is randomized between the top 3 moves
                # from the book so that same moves are not always played
                click.echo("This is from the opening book.")
                return random.choice(opening_moves[:3])

        # Check for mate in ones
        remaining_moves = san_moves.copy()
        for move in san_moves:
            test_board = board.copy()
            test_board.push_san(move)
            outcome = test_board.outcome()
            if outcome:
                if outcome.winner is self.side:
                    # Winning move is played
                    return move
                elif outcome.winner is not self.side:
                    # Losing move is removed from playable move list
                    remaining_moves.remove(move)

        if not remaining_moves:
            # All legal moves lead to loss so doesn't matter what is played
            return random.choice(san_moves)

        best_score = -1000
        for move in remaining_moves:
            test_board = board.copy()
            test_board.push_san(move)
            score_after_move = self.evaluate_board(test_board)
            if self.side is chess.BLACK:
                score_after_move *= -1
            if score_after_move > best_score:
                ok_moves = []
                ok_moves.append(move)
                best_score = score_after_move
            elif score_after_move == best_score:
                ok_moves.append(move)
        return random.choice(ok_moves)

    def check_opening_sequence(self, board: chess.Board) -> list:
        """Get all next moves suggested by an opening book.

        :param board: Current state of board
        :returns: list of decent moves
        """
        opening_moves = []
        for entry in self.opening_book.find_all(board):
            move_san = board.san(entry.move)
            opening_moves.append(move_san)
        return opening_moves

    def evaluate_board(self, board: chess.Board) -> float:
        """Calculate current game score.

        :param board: Current state of board
        :returns: current game score
        """
        total = 0
        vals = {1: 1, 2: 3, 3: 3, 4: 5, 5: 9}
        for i in range(1, 6):
            total += len(board.pieces(i, chess.WHITE)) * vals[i]
            total -= len(board.pieces(i, chess.BLACK)) * vals[i]
        return total
