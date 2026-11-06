from bots import make_bot
from cli import play_game, run_arena


def test_arena_terminates():
    assert sum(run_arena("random", "greedy", 4).values()) == 4


def test_human_bad_input_reprompts():
    inputs = iter(["zz", "a2-a5", "quit"])
    assert play_game(None, make_bot("random"), verbose=False, read=lambda _: next(inputs)) == "*"


def test_bot_game_has_result():
    result = play_game(make_bot("greedy"), make_bot("random"), verbose=False)
    assert result in {"1-0", "0-1", "1/2-1/2"}


def test_eof_at_prompt_quits():
    def read(_):
        raise EOFError
    assert play_game(None, make_bot("random"), verbose=False, read=read) == "*"
