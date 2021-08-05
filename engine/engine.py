import chess
import chess.polyglot
import click
import random
from pathlib import Path
from itertools import repeat
from pathos.pools import ProcessPool


class ChessEngine:
    """The artificial system that calculates the next move for the current game state."""

    def __init__(self, side: chess.Color):
        """Initialize the playing side and the opening book."""
        self.side = chess.WHITE if side == "White" else chess.BLACK
        self.move_evals = []
        try:
            ob_file = Path(__file__).parent / "opening_books" / ".bin"
            self.opening_book = chess.polyglot.MemoryMappedReader(ob_file)
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
        self.move_amount = len(uci_moves)

        # Play a move from the opening book if book suggests one
        if self.opening_book:
            try:
                opening_move = board.san(self.opening_book.weighted_choice(board).move)
                click.echo("This is from the opening book.")
                return opening_move
            except IndexError:
                pass

        # Search for move values
        self.move_evals = []
        '''
        with click.progressbar(uci_moves, label="Calculating", length=self.move_amount) as bar:
            # Amazing loading bar progresses with each calculated move
            for move in bar:
                self.search_initializer(move, board)
        '''
        # Multiprocess searching
        pool = ProcessPool(6)
        board_list = [board for i in range(self.move_amount)]
        self.move_evals = pool.map(self.search_initializer, uci_moves, board_list)

        # Rank worthiest moves
        self.move_evals.sort(key = lambda x: x[1])
        self.move_evals.reverse()
        remaining_moves = []
        for i in self.move_evals:
            if self.move_evals[0][1] == i[1]:
                remaining_moves.append(board.san(i[0]))
            else:
                break

        # Pick one of the worthiest moves
        reasoning = (f"Total moves: {self.move_amount}\nPossible best moves: " +
        f"{remaining_moves}\nWith evaluated score: {self.move_evals[0][1]/100}\n")
        random.shuffle(remaining_moves)
        click.echo(reasoning)
        return remaining_moves[0]

    def search_initializer(self, move: chess.Move, board: chess.Board):
        """Begin searching and evaluating values for a move."""
        depth = 1
        if self.move_amount >= 36:
            depth = 1
        elif self.move_amount >= 26 or len(board.piece_map()) <= 28:
            depth = 2
        elif self.move_amount >= 18 or len(board.piece_map()) <= 22:
            depth = 3
        elif self.move_amount < 18 or len(board.piece_map()) <= 8:
            depth = 6
        board.push(move)
        score = -self.alphaBeta(board, -100000, 100000, depth)
        board.pop()
        return (move, score)

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

    def evaluate_board(self, board: chess.Board) -> int:
        """Calculate current game score.

        :param board: Current state of board
        :returns: current game score
        """
        piece = {1: 100, 2:300, 3:300, 4:500, 5:900, 6:500}
        # Piece square tables
        pst = {
            1: [0,  0,  0,  0,  0,  0,  0,  0,
                5, 10, 10,-25,-25, 10, 10,  5,
                5, -5,-10,  0,  0,-10, -5,  5,
                5,  0,  0, 25, 25,  0,  0,  5,
                5,  5, 10, 27, 27, 10,  5,  5,
                10, 10, 20, 30, 30, 20, 10, 10,
                50, 50, 50, 50, 50, 50, 50, 50,
                0,  0,  0,  0,  0,  0,  0,  0],

            2: [-50,-40,-30,-30,-30,-30,-40,-50,
                -40,-20,  0,  0,  0,  0,-20,-40,
                -30,  0, 10, 15, 15, 10,  0,-30,
                -30,  5, 15, 20, 20, 15,  5,-30,
                -30,  0, 15, 20, 20, 15,  0,-30,
                -30,  5, 10, 15, 15, 10,  5,-30,
                -40,-20,  0,  5,  5,  0,-20,-40,
                -50,-40,-20,-30,-30,-20,-40,-50,],

            3: [-20,-10,-10,-10,-10,-10,-10,-20,
                -10, 15,  0,  0,  0,  0, 15,-10,
                -10, 10, 10, 10, 10, 10, 10,-10,
                -10,  0, 15, 10, 10, 15,  0,-10,
                -10,  5,  5, 10, 10,  5,  5,-10,
                -10,  0,  5, 10, 10,  5,  0,-10,
                -10,  0,  0,  0,  0,  0,  0,-10,
                -20,-10,-40,-10,-10,-40,-10,-20,],

            4: [0] * 64, 5: [0] * 64,

            6: [ 20,  30,  10,   0,   0,  10,  30,  20,
                 20,  20,   0,   0,   0,   0,  20,  20,
                -10, -20, -20, -20, -20, -20, -20, -10,
                -20, -30, -30, -40, -40, -30, -30, -20,
                -30, -40, -40, -50, -50, -40, -40, -30,
                -30, -40, -40, -50, -50, -40, -40, -30,
                -30, -40, -40, -50, -50, -40, -40, -30,
                -30, -40, -40, -50, -50, -40, -40, -30]
        }
        score = 0
        for pos in board.piece_map():
            if board.color_at(pos):
                score += pst[board.piece_type_at(pos)][pos] + piece[board.piece_type_at(pos)]
            else:
                score -= pst[board.piece_type_at(pos)][63 - pos] + piece[board.piece_type_at(pos)]
        return score if board.turn else -score

    def quiesce(self, board: chess.Board, alpha: int, beta: int) -> int:
        """Check until game state is calm and quiet."""
        stand_pat = self.evaluate_board(board)
        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat
        for move in board.legal_moves:
            if board.is_capture(move):
                board.push(move)
                score = -self.quiesce(board, -beta, -alpha)
                board.pop()
                if score > alpha:
                    if score >= beta:
                        return beta
                    alpha = score
        return alpha

    def negamax_search(self, board: chess.Board, depth: int) -> int:
        """Search move values at specific depth with negamax.

        :param board: Current state of board
        :param depth: Depth of search
        """
        if depth == 0:
            return self.evaluate_board(board)
        maxScore = -1000
        for move in board.legal_moves:
            board.push(move)
            score = -self.negamax_search(board, depth - 1)
            if score > maxScore:
                maxScore = score
            board.pop()
        return maxScore

    def alphaBeta(self, board: chess.Board, alpha: int, beta: int, depth: int) -> int:
        """Execute alpha beta pruning."""
        if board.outcome():
            # Test for mates and draws
            return alpha if board.is_checkmate() else 0
        if depth == 0:
            return self.quiesce(board, alpha, beta)
        moves = self.ordered(board)
        for move in moves:
            board.push(move)
            score = -self.alphaBeta(board, -beta, -alpha, depth - 1)
            board.pop()
            if score > alpha:
                if score >= beta:
                    return beta
                alpha = score
        return alpha

    def ordered(self, board: chess.Board) -> list:
        """Order legal moves by captures."""
        moves = []
        for move in board.legal_moves:
            if board.is_capture(move):
                moves.insert(0, move)
            else:
                moves.append(move)
        return moves
