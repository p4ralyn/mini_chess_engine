"""Terminal minichess: play a bot or run a bot-vs-bot arena.

    python cli.py --white human --black minimax3
    python cli.py --white minimax3 --black greedy --games 20
"""
import argparse
import time

from board import WHITE, Board, move_to_str, parse_move
from bots import BOT_NAMES, make_bot


def play_game(white, black, delay: float = 0.0, verbose: bool = True, read=input) -> str:
    """Play one game (None = human) and return the result string."""
    board = Board()
    while board.game_over_reason() is None:
        if verbose:
            print(board, "\n")
        player = (white, black)[board.turn]
        if player is None:
            move = None
            while move is None:
                side = "white" if board.turn == WHITE else "black"
                try:
                    text = read(f"{side} move (or quit): ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    return "*"
                if text == "quit":
                    return "*"
                move = parse_move(board, text)
                if move is None:
                    print("illegal move, try again")
        else:
            move = player.get_move(board)
            time.sleep(delay)
        if verbose:
            print(f"{'white' if board.turn == WHITE else 'black'}: {move_to_str(board, move)}")
        board = board.make_move(move)
    if verbose:
        print(board, "\n")
        print(f"{board.game_over_reason()}: {board.result()}")
    return board.result() or "*"


def run_arena(name_a: str, name_b: str, games: int) -> dict[str, int]:
    """Play games between two bots, alternating colors, and tally wins."""
    key_a, key_b = (name_a + " (1)", name_b + " (2)") if name_a == name_b else (name_a, name_b)
    tally = {key_a: 0, key_b: 0, "draw": 0}
    for i in range(games):
        a_white = i % 2 == 0
        a, b = make_bot(name_a), make_bot(name_b)
        result = play_game(a if a_white else b, b if a_white else a, verbose=False)
        if result == "1/2-1/2":
            tally["draw"] += 1
        elif (result == "1-0") == a_white:
            tally[key_a] += 1
        else:
            tally[key_b] += 1
    return tally


def _parse_args() -> argparse.Namespace:
    """Read and check command line options."""
    parser = argparse.ArgumentParser(description="4x5 Silverman minichess")
    choices = ["human"] + BOT_NAMES
    parser.add_argument("--white", default="human", choices=choices)
    parser.add_argument("--black", default="minimax3", choices=choices)
    parser.add_argument("--games", type=int, default=1)
    parser.add_argument("--delay", type=float, default=0.0)
    args = parser.parse_args()
    if args.games < 1:
        parser.error("--games must be at least 1")
    if args.games > 1 and "human" in (args.white, args.black):
        parser.error("--games > 1 needs two bots")
    return args


def main() -> None:
    """Run one game or an arena."""
    args = _parse_args()
    if args.games > 1:
        tally = run_arena(args.white, args.black, args.games)
        a, b = [k for k in tally if k != "draw"]
        print(f"{a} wins: {tally[a]}  {b} wins: {tally[b]}  draws: {tally['draw']}")
    else:
        play_game(make_bot(args.white), make_bot(args.black), args.delay)


if __name__ == "__main__":
    main()
