# mini_chess_engine

Minichess engine for CSD311 Artificial Intelligence. Plays 4x5 Silverman minichess with random, greedy and minimax (alpha-beta) bots, from the terminal or a pygame window.

## Rules

4 files (a-d) x 5 ranks.

```
5  r q k r
4  p p p p
3  . . . .
2  P P P P
1  R Q K R
   a b c d
```

- pieces: pawn, rook, queen, king
- pawns move one square, or two from their starting rank if both squares are empty, and capture diagonally
- a pawn reaching the last rank becomes a queen
- no castling, no en passant
- game ends on checkmate, stalemate (draw), 50 plies with no capture or pawn move (draw), or threefold repetition (draw)

Moves are written `a2-a3`, captures `b2xc3`, promotions `a4-a5=Q`. In the terminal `a2a3` works too.

## Setup

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Uses `pygame-ce` (same `import pygame`, has wheels for newer python versions).

## Running

GUI, pick each side with the `<` `>` buttons (human, random, greedy, minimax2-5):

```
python gui.py
```

Terminal game:

```
python cli.py --white human --black minimax3
```

Bot vs bot arena (colours swap every game):

```
python cli.py --white minimax4 --black minimax3 --games 20
```

## Bots

- **random** - any legal move
- **greedy** - best material after one move, small bonus for pushing pawns, ties broken randomly
- **minimaxN** - negamax with alpha-beta pruning to depth N (2-5)
  - move ordering: promotions first, then captures by MVV-LVA (most valuable victim, least valuable attacker), then the rest
  - eval: material (P=1, R=5, Q=9) + 0.1 per rank a pawn has advanced
  - mate scored as `MATE - ply` so it goes for the fastest mate
  - equal moves are shuffled so games are not all identical

Depth 5 takes well under a second per move on this board.

Arena results (20 games each):

| match | wins | losses | draws |
|---|---|---|---|
| greedy vs random | 5 | 0 | 15 |
| minimax2 vs greedy | 18 | 0 | 2 |
| minimax3 vs minimax2 | 10 | 3 | 7 |
| minimax4 vs minimax3 | 14 | 3 | 3 |
| minimax5 vs minimax3 | 20 | 0 | 0 |

## Board representation

The board is stored as bitboards: one int per (colour, piece), 8 ints for 20 squares, square index `rank * 4 + file`. King and pawn attacks are precomputed per square, rooks and queens walk precomputed rays until they hit a piece. `make_move` returns a new board instead of undoing moves.

## Files

```
board.py       rules, move generation, bitboards
bots.py        random, greedy, minimax bots + evaluation
cli.py         terminal game and arena
gui.py         pygame interface
test_board.py  rules tests (perft checked against a separate slow move generator)
test_bots.py   bot tests (mate in one, takes free queen, ...)
test_cli.py    cli and arena tests
```

## Tests

```
pytest
```

## Credits

Ideas taken from two seniors' repos: [trishaladabala/ChessBots](https://github.com/trishaladabala/ChessBots) (minichess variant, bot lineup, pygame interface) and [ApaarRaina/Chess_Engine](https://github.com/ApaarRaina/Chess_Engine) (bitboard encoding).
