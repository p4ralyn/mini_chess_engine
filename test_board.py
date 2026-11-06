from board import (BLACK, WHITE, QUEEN, Board, Move, move_to_str, parse_move,
                   square_index, square_name)

START_ROWS = ["rqkr", "pppp", "....", "PPPP", "RQKR"]
MID_ROWS_1 = ["r.kr", "pq.p", "..P.", "PP.P", "RQKR"]
MID_ROWS_2 = ["r.k.", "p..p", ".Q..", "P..P", "R.K."]


def perft(b, depth):
    if depth == 0:
        return 1
    return sum(perft(b.make_move(m), depth - 1) for m in b.legal_moves())


# Slow independent reference on a 5x4 grid (grid[rank][file], rank 0 = rank 1)
def to_grid(rows):
    return [list(r) for r in reversed(rows)]


def is_white(ch):
    return ch.isupper()


def ref_attacked(grid, r, f, by_white):
    for rr in range(5):
        for ff in range(4):
            ch = grid[rr][ff]
            if ch == "." or is_white(ch) != by_white:
                continue
            dr, df = r - rr, f - ff
            p = ch.upper()
            if p == "K" and max(abs(dr), abs(df)) == 1:
                return True
            if p == "P" and df in (-1, 1) and dr == (1 if by_white else -1):
                return True
            if p in "RQ":
                orth = (dr == 0) != (df == 0)
                diag = abs(dr) == abs(df) != 0
                if (orth or (diag and p == "Q")):
                    sr = (dr > 0) - (dr < 0)
                    sf = (df > 0) - (df < 0)
                    x, y = rr + sr, ff + sf
                    while (x, y) != (r, f) and grid[x][y] == ".":
                        x, y = x + sr, y + sf
                    if (x, y) == (r, f):
                        return True
    return False


def ref_moves(grid, white):
    out = []
    for r in range(5):
        for f in range(4):
            ch = grid[r][f]
            if ch == "." or is_white(ch) != white:
                continue
            p = ch.upper()
            targets = []
            if p == "P":
                d = 1 if white else -1
                if 0 <= r + d < 5 and grid[r + d][f] == ".":
                    targets.append((r + d, f))
                    if r == (1 if white else 3) and grid[r + 2 * d][f] == ".":
                        targets.append((r + 2 * d, f))
                for df in (-1, 1):
                    x, y = r + d, f + df
                    if 0 <= x < 5 and 0 <= y < 4 and grid[x][y] != "." and is_white(grid[x][y]) != white:
                        targets.append((x, y))
            else:
                if p == "K":
                    dirs, reach = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b], 1
                elif p == "R":
                    dirs, reach = [(1, 0), (-1, 0), (0, 1), (0, -1)], 4
                else:
                    dirs, reach = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b], 4
                for a, b in dirs:
                    x, y = r + a, f + b
                    for _ in range(reach):
                        if not (0 <= x < 5 and 0 <= y < 4):
                            break
                        if grid[x][y] == ".":
                            targets.append((x, y))
                        else:
                            if is_white(grid[x][y]) != white:
                                targets.append((x, y))
                            break
                        x, y = x + a, y + b
            for x, y in targets:
                out.append(((r, f), (x, y)))
    return out


def ref_apply(grid, mv):
    (r, f), (x, y) = mv
    g = [row[:] for row in grid]
    ch = g[r][f]
    g[r][f] = "."
    if ch.upper() == "P" and x in (0, 4):
        ch = "Q" if ch == "P" else "q"
    g[x][y] = ch
    return g


def ref_perft(grid, white, depth):
    if depth == 0:
        return 1
    king = "K" if white else "k"
    total = 0
    for mv in ref_moves(grid, white):
        g = ref_apply(grid, mv)
        kr, kf = next((r, f) for r in range(5) for f in range(4) if g[r][f] == king)
        if not ref_attacked(g, kr, kf, not white):
            total += ref_perft(g, not white, depth - 1)
    return total


def moves_of(b):
    return sorted(move_to_str(b, m) for m in b.legal_moves())


def test_start_moves():
    b = Board()
    assert moves_of(b) == ["a2-a3", "b2-b3", "c2-c3", "d2-d3"]


def test_square_names():
    assert square_name(0) == "a1"
    assert square_name(19) == "d5"
    assert square_index("c4") == 14


def test_perft_matches_reference():
    cases = [(Board(), START_ROWS, WHITE),
             (Board.from_rows(MID_ROWS_1), MID_ROWS_1, WHITE),
             (Board.from_rows(MID_ROWS_2, BLACK), MID_ROWS_2, BLACK)]
    for b, rows, turn in cases:
        for depth in range(1, 5):
            assert perft(b, depth) == ref_perft(to_grid(rows), turn == WHITE, depth)


def test_double_step():
    b = Board.from_rows(["k...", "....", "....", ".P..", "...K"])
    assert {"b2-b3", "b2-b4"} <= set(moves_of(b))
    b = Board.from_rows(["k...", "....", ".r..", ".P..", "...K"])
    assert not {"b2-b3", "b2-b4"} & set(moves_of(b))
    b = Board.from_rows(["k...", "....", ".P..", "....", "...K"])
    assert "b3-b5" not in moves_of(b)


def test_promotion():
    b = Board.from_rows(["..k.", "P...", "....", "....", "...K"])
    assert "a4-a5=Q" in moves_of(b)
    after = b.make_move(parse_move(b, "a4-a5=Q"))
    assert after.piece_at(16) == (WHITE, QUEEN)
    b = Board.from_rows([".rk.", "P...", "....", "....", "...K"])
    assert "a4xb5=Q" in moves_of(b)


def test_checkmate():
    b = Board.from_rows(["k...", ".Q..", ".K..", "....", "...."], BLACK)
    assert b.game_over_reason() == "checkmate"
    assert b.result() == "1-0"


def test_stalemate():
    b = Board.from_rows(["k...", "..Q.", ".K..", "....", "...."], BLACK)
    assert b.game_over_reason() == "stalemate"
    assert b.result() == "1/2-1/2"


def test_cannot_leave_king_in_check():
    # white rook a2 is pinned to its king by the black rook on a5
    b = Board.from_rows(["r..k", "....", "....", "R...", "K..."])
    rook_moves = [m for m in b.legal_moves() if m.frm == 4]
    assert all(m.to % 4 == 0 for m in rook_moves)
    assert {"a2-a3", "a2-a4", "a2xa5"} <= set(moves_of(b))
    assert "a2-b2" not in moves_of(b)


def test_repetition_and_fifty():
    b = Board.from_rows(["k...", "....", "....", "....", "K..R"])
    for _ in range(2):
        assert b.game_over_reason() is None
        for text in ("d1-d2", "a5-b5", "d2-d1", "b5-a5"):
            b = b.make_move(parse_move(b, text))
    assert b.game_over_reason() == "repetition"
    assert Board(halfmove_clock=50).game_over_reason() == "50-move rule"


def test_parse_move_rejects_illegal():
    b = Board()
    assert parse_move(b, "a2-a5") is None
    assert parse_move(b, "zz") is None
    assert parse_move(b, "") is None
    assert parse_move(b, "A2A3") == Move(4, 8)
