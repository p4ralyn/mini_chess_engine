import pytest

from board import BLACK, Board, Move, square_index
from bots import BOT_NAMES, GreedyBot, MinimaxBot, RandomBot, evaluate, make_bot


def test_evaluate_start_is_zero():
    assert evaluate(Board()) == 0


def test_minimax_finds_mate_in_one():
    # only Rc2-c5 mates: Ka3 covers a4/b4, Rb1 covers b-file, so Rb1-b5 just loses the rook
    b = Board.from_rows(["k...", "....", "K...", "..R.", ".R.."])
    mate = Move(square_index("c2"), square_index("c5"))
    for depth in (2, 3):
        assert MinimaxBot(depth).get_move(b) == mate


def test_greedy_takes_free_queen():
    b = Board.from_rows(["...k", "....", "...q", "....", "K..R"])
    assert GreedyBot().get_move(b) == Move(square_index("d1"), square_index("d3"))


def test_bots_return_none_when_no_moves():
    b = Board.from_rows(["k...", ".Q..", ".K..", "....", "...."], BLACK)
    for bot in (RandomBot(), GreedyBot(), MinimaxBot(2)):
        assert bot.get_move(b) is None


def test_make_bot():
    for name in BOT_NAMES:
        assert make_bot(name).name == name
    assert make_bot("human") is None
    with pytest.raises(ValueError):
        make_bot("bogus")


def test_minimax_prefers_fastest_mate():
    # same position as the mate-in-1 test: slower mates exist, the fast one must win
    b = Board.from_rows(["k...", "....", "K...", "..R.", ".R.."])
    mate = Move(square_index("c2"), square_index("c5"))
    for _ in range(5):
        assert MinimaxBot(4).get_move(b) == mate
