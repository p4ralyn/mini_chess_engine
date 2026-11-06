"""Random, greedy and minimax players."""
import random

from board import BLACK, KING, PAWN, QUEEN, ROOK, WHITE, Board, Move, RANKS, _bits

PIECE_VALUES = {PAWN: 1, ROOK: 5, QUEEN: 9, KING: 0}
MATE = 10000
BOT_NAMES = ["random", "greedy", "minimax2", "minimax3", "minimax4", "minimax5"]


def evaluate(board: Board) -> float:
    """Material plus pawn advancement, from the side to move's view."""
    score = 0.0
    for color in (WHITE, BLACK):
        sign = 1 if color == board.turn else -1
        for piece, value in PIECE_VALUES.items():
            bb = board.bitboards[color * 4 + piece]
            score += sign * value * bb.bit_count()
        for sq in _bits(board.bitboards[color * 4 + PAWN]):
            rank = sq // 4
            score += sign * 0.1 * (rank - 1 if color == WHITE else RANKS - 2 - rank)
    return score


class RandomBot:
    name = "random"

    def get_move(self, board: Board) -> Move | None:
        moves = board.legal_moves()
        return random.choice(moves) if moves else None


class GreedyBot:
    name = "greedy"

    def get_move(self, board: Board) -> Move | None:
        moves = board.legal_moves()
        if not moves:
            return None
        # evaluate is from the opponent's view after the move, so lower is better
        scored = [(-evaluate(board.make_move(m)), m) for m in moves]
        best = max(s for s, _ in scored)
        return random.choice([m for s, m in scored if s == best])


class MinimaxBot:
    def __init__(self, depth: int = 3):
        self.depth = depth
        self.name = f"minimax{depth}"
        self.nodes = 0

    def _order_key(self, board: Board, move: Move) -> int:
        if move.promo:
            return -1000
        victim = board.piece_at(move.to)
        if victim is None:
            return 0
        attacker = board.piece_at(move.frm)[1]
        return -(PIECE_VALUES[victim[1]] * 10 - PIECE_VALUES[attacker])

    def _ordered(self, board: Board, moves: list[Move]) -> list[Move]:
        random.shuffle(moves)
        return sorted(moves, key=lambda m: self._order_key(board, m))

    def _negamax(self, board: Board, depth: int, alpha: float, beta: float, ply: int) -> float:
        self.nodes += 1
        moves = board.legal_moves()
        if not moves:
            return -(MATE - ply) if board.is_in_check(board.turn) else 0
        if board.halfmove_clock >= 50 or board.history.get(board.key(), 0) >= 3:
            return 0
        if depth == 0:
            return evaluate(board)
        for m in self._ordered(board, moves):
            score = -self._negamax(board.make_move(m), depth - 1, -beta, -alpha, ply + 1)
            if score >= beta:
                return score
            alpha = max(alpha, score)
        return alpha

    def get_move(self, board: Board) -> Move | None:
        self.nodes = 0
        moves = board.legal_moves()
        if not moves:
            return None
        best, alpha = None, -float("inf")
        for m in self._ordered(board, moves):
            score = -self._negamax(board.make_move(m), self.depth - 1, -float("inf"), -alpha, 1)
            if score > alpha:
                best, alpha = m, score
        return best


def make_bot(name: str):
    """Bot for a menu name; None for a human player."""
    if name == "human":
        return None
    if name == "random":
        return RandomBot()
    if name == "greedy":
        return GreedyBot()
    if name in BOT_NAMES:
        return MinimaxBot(int(name[len("minimax"):]))
    raise ValueError(f"unknown bot: {name}")
