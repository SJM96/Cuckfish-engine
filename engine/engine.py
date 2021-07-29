import chess
import chess.polyglot
import click
import random
from pathlib import Path


class ChessEngine:
    """The artificial system that calculates the next move for the current game state."""

    def __init__(self, side: chess.Color, depth: int):
        """Initialize the playing side and the opening book."""
        self.side = chess.WHITE if side == "White" else chess.BLACK
        self.depth = depth
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

        # Play a move from the opening book if book suggests one
        if self.opening_book:
            opening_moves = self.check_opening_sequence(board)
            if opening_moves:
                # Choice is randomized between the top 3 moves
                # from the book so that same moves are not always played
                click.echo("This is from the opening book.")
                return random.choice(opening_moves[:3])

        # Search for move values
        depth = self.depth
        maxScore = -1000
        move_evals = []
        with click.progressbar(uci_moves, label="Calculating", length=len(uci_moves)) as bar:
            # Amazing loading bar progresses with each calculated move
            for move in bar:
                board.push(move)
                score = -self.search(board, depth - 1)
                if score > maxScore:
                    maxScore = score
                move_evals.append((move, score))
                board.pop()
            move_evals.sort(key = lambda x: x[1])
            move_evals.reverse()

        # Rank worthiest moves
        remaining_moves = []
        for i in move_evals:
            if move_evals[0][1] == i[1]:
                remaining_moves.append(board.san(i[0]))
            else:
                break

        # Pick one of the worthiest moves
        random.shuffle(remaining_moves)
        click.echo(remaining_moves)
        return remaining_moves[0]

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

    def evaluate_board(self, board: chess.Board, color: chess.Color) -> float:
        """Calculate current game score.

        :param board: Current state of board
        :returns: current game score
        """
        total = 0
        vals = {1: 1, 2: 3, 3: 3, 4: 5, 5: 9}
        for i in range(1, 6):
            total += len(board.pieces(i, chess.WHITE)) * vals[i]
            total -= len(board.pieces(i, chess.BLACK)) * vals[i]
        return total if color else total * -1

    def search(self, board: chess.Board, depth: int) -> int:
        """Search move values at specific depth.

        :param board: Current state of board
        :param depth: Depth of search
        """
        if depth == 0:
            return self.evaluate_board(board, board.turn)
        maxScore = -1000
        for move in board.legal_moves:
            board.push(move)
            score = -self.search(board, depth - 1)
            if score > maxScore:
                maxScore = score
            board.pop()
        return maxScore
