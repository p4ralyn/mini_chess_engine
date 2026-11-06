"""4x5 Silverman minichess rules on bitboards."""
import re
from collections.abc import Iterable, Iterator
from typing import NamedTuple

WHITE, BLACK = 0, 1
PAWN, ROOK, QUEEN, KING = 0, 1, 2, 3
FILES, RANKS = 4, 5
LETTERS = "PRQK"


class Move(NamedTuple):
    frm: int
    to: int
    promo: bool = False


def square_name(sq: int) -> str:
    """Name of a square index, like a1."""
    return "abcd"[sq % FILES] + str(sq // FILES + 1)


def square_index(name: str) -> int:
    """Index of a square name, like a1."""
    return (int(name[1]) - 1) * FILES + "abcd".index(name[0])


def _on_board(f: int, r: int) -> bool:
    return 0 <= f < FILES and 0 <= r < RANKS


def _mask(squares: Iterable[int]) -> int:
    return sum(1 << s for s in squares)


def bits(mask: int) -> Iterator[int]:
    """Indexes of the set bits."""
    while mask:
        low = mask & -mask
        yield low.bit_length() - 1
        mask ^= low


def _ray(sq: int, df: int, dr: int) -> list[int]:
    out, f, r = [], sq % FILES + df, sq // FILES + dr
    while _on_board(f, r):
        out.append(r * FILES + f)
        f, r = f + df, r + dr
    return out


ORTHO = [(1, 0), (-1, 0), (0, 1), (0, -1)]
DIAG = [(1, 1), (1, -1), (-1, 1), (-1, -1)]

# per-square tables, built once
KING_ATT = [_mask(s2 for df, dr in ORTHO + DIAG for s2 in _ray(s, df, dr)[:1]) for s in range(20)]
PAWN_ATT = [[_mask(s2 for df in (1, -1) for s2 in _ray(s, df, d)[:1]) for s in range(20)]
            for d in (1, -1)]  # indexed [color][sq]
ORTHO_RAYS = [[_ray(s, df, dr) for df, dr in ORTHO] for s in range(20)]
DIAG_RAYS = [[_ray(s, df, dr) for df, dr in DIAG] for s in range(20)]


def _slide(sq: int, rays: list[list[list[int]]], occ: int) -> int:
    """Squares reached along the rays, stopping at (and including) the first blocker."""
    out = 0
    for ray in rays[sq]:
        for s in ray:
            out |= 1 << s
            if occ >> s & 1:
                break
    return out


START_ROWS = ["rqkr", "pppp", "....", "PPPP", "RQKR"]


class Board:
    """Position, side to move and draw counters."""

    def __init__(self, bitboards: list[int] | None = None, turn: int = WHITE,
                 halfmove_clock: int = 0, history: dict | None = None):
        if bitboards is None:
            bitboards = self._parse_rows(START_ROWS)
        self.bitboards = bitboards
        self.turn = turn
        self.halfmove_clock = halfmove_clock
        self.history = history if history is not None else {self.key(): 1}

    @staticmethod
    def _parse_rows(rows: list[str]) -> list[int]:
        bbs = [0] * 8
        for i, row in enumerate(rows):
            for f, ch in enumerate(row):
                if ch != ".":
                    color = WHITE if ch.isupper() else BLACK
                    bbs[color * 4 + LETTERS.index(ch.upper())] |= 1 << ((RANKS - 1 - i) * FILES + f)
        return bbs

    @classmethod
    def from_rows(cls, rows: list[str], turn: int = WHITE) -> "Board":
        """Board from rank strings, rank 5 first."""
        return cls(cls._parse_rows(rows), turn)

    def key(self) -> tuple:
        """Hashable position for repetition counting."""
        return (tuple(self.bitboards), self.turn)

    def piece_at(self, sq: int) -> tuple[int, int] | None:
        """(color, piece) on sq, or None."""
        for i, bb in enumerate(self.bitboards):
            if bb >> sq & 1:
                return divmod(i, 4)
        return None

    def occupied(self, color: int | None = None) -> int:
        """Mask of one side's pieces, or both."""
        if color is None:
            return self.occupied(WHITE) | self.occupied(BLACK)
        return sum(self.bitboards[color * 4:color * 4 + 4])  # masks never overlap

    def _attacked(self, sq: int, by: int) -> bool:
        bb, occ = self.bitboards, self.occupied()
        rq = bb[by * 4 + ROOK] | bb[by * 4 + QUEEN]
        return bool(PAWN_ATT[1 - by][sq] & bb[by * 4 + PAWN]
                    or KING_ATT[sq] & bb[by * 4 + KING]
                    or _slide(sq, ORTHO_RAYS, occ) & rq
                    or _slide(sq, DIAG_RAYS, occ) & bb[by * 4 + QUEEN])

    def is_in_check(self, color: int) -> bool:
        """True if color's king is attacked."""
        king = self.bitboards[color * 4 + KING]
        return bool(king) and self._attacked(king.bit_length() - 1, 1 - color)

    def _pseudo_moves(self) -> list[Move]:
        me, occ = self.turn, self.occupied()
        own, enemy = self.occupied(me), self.occupied(1 - me)
        moves = []
        for piece in range(4):
            for sq in bits(self.bitboards[me * 4 + piece]):
                if piece == PAWN:
                    step = FILES if me == WHITE else -FILES
                    targets = PAWN_ATT[me][sq] & enemy
                    if not occ >> (sq + step) & 1:
                        targets |= 1 << (sq + step)
                        start = 1 if me == WHITE else 3
                        if sq // FILES == start and not occ >> (sq + 2 * step) & 1:
                            targets |= 1 << (sq + 2 * step)
                    last = RANKS - 1 if me == WHITE else 0
                    moves += [Move(sq, t, t // FILES == last) for t in bits(targets)]
                    continue
                if piece == KING:
                    targets = KING_ATT[sq]
                else:
                    targets = _slide(sq, ORTHO_RAYS, occ)
                    if piece == QUEEN:
                        targets |= _slide(sq, DIAG_RAYS, occ)
                moves += [Move(sq, t) for t in bits(targets & ~own)]
        return moves

    def legal_moves(self) -> list[Move]:
        """All legal moves for the side to move."""
        return [m for m in self._pseudo_moves() if not self.make_move(m).is_in_check(self.turn)]

    def is_capture(self, move: Move) -> bool:
        """True if the move lands on an enemy piece."""
        return bool(self.occupied(1 - self.turn) >> move.to & 1)

    def make_move(self, move: Move) -> "Board":
        """New board after the move."""
        me = self.turn
        piece = self.piece_at(move.frm)[1]  # type: ignore[index]
        capture = self.is_capture(move)
        bbs = list(self.bitboards)
        for i in range((1 - me) * 4, (1 - me) * 4 + 4):
            bbs[i] &= ~(1 << move.to)
        bbs[me * 4 + piece] &= ~(1 << move.frm)
        bbs[me * 4 + (QUEEN if move.promo else piece)] |= 1 << move.to
        clock = 0 if capture or piece == PAWN else self.halfmove_clock + 1
        new = Board(bbs, 1 - me, clock, dict(self.history))
        new.history[new.key()] = new.history.get(new.key(), 0) + 1
        return new

    def game_over_reason(self) -> str | None:
        """Why the game ended, or None."""
        if not self.legal_moves():
            return "checkmate" if self.is_in_check(self.turn) else "stalemate"
        if self.halfmove_clock >= 50:
            return "50-ply rule"
        if self.history.get(self.key(), 0) >= 3:
            return "repetition"
        return None

    def result(self) -> str | None:
        """1-0, 0-1, 1/2-1/2, or None while playing."""
        reason = self.game_over_reason()
        if reason is None:
            return None
        if reason == "checkmate":
            return "0-1" if self.turn == WHITE else "1-0"
        return "1/2-1/2"

    def __str__(self) -> str:
        lines = []
        for r in range(RANKS - 1, -1, -1):
            cells = []
            for f in range(FILES):
                p = self.piece_at(r * FILES + f)
                cells.append("." if p is None else LETTERS[p[1]].lower() if p[0] == BLACK else LETTERS[p[1]])
            lines.append(f"{r + 1} " + " ".join(cells))
        return "\n".join(lines + ["  a b c d"])


def move_to_str(board: Board, move: Move) -> str:
    """Move as text, like a2-a3 or b1xb5."""
    sep = "x" if board.is_capture(move) else "-"
    return square_name(move.frm) + sep + square_name(move.to) + ("=Q" if move.promo else "")


def parse_move(board: Board, text: str) -> Move | None:
    """Legal move matching the text, or None."""
    m = re.fullmatch(r"([a-d][1-5])[-x]?([a-d][1-5])(=q)?", text.lower().replace(" ", ""))
    if not m:
        return None
    frm, to = square_index(m[1]), square_index(m[2])
    return next((mv for mv in board.legal_moves() if mv.frm == frm and mv.to == to), None)
