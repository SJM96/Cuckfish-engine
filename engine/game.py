import click
import chess
from progress.bar import Bar
from time import sleep
from .engine import ChessEngine


class ChessGame:
    """Class for creating and playing a game of chess against the engine."""

    def __init__(self):
        """Initiate a game instance."""
        self.board = chess.Board()
        self.engine = ChessEngine()
        player_choice = None
        while player_choice is None:
            player_choice = self.choose_side()
        self.player_color = "White" if player_choice else "Black"
        self.engine_color = "White" if not player_choice else "Black"
        self.player_move() if player_choice else self.engine_move()

    def choose_side(self):
        """Set which color the player wants to play as."""
        choice = click.prompt("Play as white or black (w/b)")
        click.echo()
        if choice == "w":
            return chess.WHITE
        elif choice == "b":
            return chess.BLACK
        else:
            return None

    def player_move(self):
        """Update the board according to which move the player makes."""
        try:
            move = click.prompt(self.player_color + " plays", type=str)
            click.echo()
            self.board.push_san(move)
            self.engine_move()
        except ValueError:
            click.echo("Given input is not standard algebraic notation of a legal move in this position")
            self.player_move()

    def engine_move(self):
        """Update the board according to which move the engine makes."""
        moves = list(self.board.legal_moves)
        with click.progressbar(moves, label="Calculating") as bar:
            for i in bar:
                sleep(0.05)
        move = self.engine.next_move(self.board)
        # move_san = self.board.san(move)
        self.board.push_san(move)
        click.echo("-"*15)
        click.echo(self.board)
        click.echo("-"*15)
        click.echo(self.engine_color + " plays: " + move)
        click.echo()
        self.player_move()
