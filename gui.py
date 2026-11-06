"""Pygame minichess: human vs bot or bot vs bot."""
import pygame

from board import (
    BLACK,
    FILES,
    KING,
    PAWN,
    QUEEN,
    RANKS,
    ROOK,
    WHITE,
    Board,
    Move,
    move_to_str,
    square_name,
)
from bots import BOT_NAMES, make_bot

SQUARE = 100
BOARD_W, BOARD_H = FILES * SQUARE, RANKS * SQUARE
PANEL_W = 260
LIGHT, DARK, HIGHLIGHT = "#F0D9B5", "#B58863", "#769656"
PANEL_BG, TEXT, BUTTON = "#262522", "#EEEEEE", "#4A4845"
GLYPHS = {(WHITE, KING): "♔", (WHITE, QUEEN): "♕", (WHITE, ROOK): "♖", (WHITE, PAWN): "♙",
          (BLACK, KING): "♚", (BLACK, QUEEN): "♛", (BLACK, ROOK): "♜", (BLACK, PAWN): "♟"}
LETTERS = {KING: "K", QUEEN: "Q", ROOK: "R", PAWN: "P"}
CHOICES = ["human"] + BOT_NAMES
MOVES_SHOWN = 12


class Game:
    """Current board, selection, move list and who plays each side."""

    def __init__(self, white: str, black: str):
        self.names = [white, black]
        self.new_game()

    def new_game(self) -> None:
        """Reset the board and rebuild the bots."""
        self.board = Board()
        self.bots = [make_bot(n) for n in self.names]
        self.selected: int | None = None
        self.moves: list[str] = []

    def play(self, move: Move) -> None:
        """Apply a move and log it."""
        self.moves.append(move_to_str(self.board, move))
        self.board = self.board.make_move(move)
        self.selected = None

    def cycle(self, color: int, step: int) -> None:
        """Switch a side to the next or previous player and restart."""
        self.names[color] = CHOICES[(CHOICES.index(self.names[color]) + step) % len(CHOICES)]
        self.new_game()

    def click_square(self, sq: int) -> None:
        """Select an own piece or move the selected piece to sq."""
        for m in self.board.legal_moves():
            if m.frm == self.selected and m.to == sq:
                self.play(m)
                return
        piece = self.board.piece_at(sq)
        self.selected = sq if piece and piece[0] == self.board.turn else None

    def status(self) -> str:
        """Status line text."""
        reason = self.board.game_over_reason()
        if reason:
            return f"{reason}: {self.board.result()}"
        side = "White" if self.board.turn == WHITE else "Black"
        return f"{side} to move" + (" (check)" if self.board.is_in_check(self.board.turn) else "")


def square_rect(sq: int) -> pygame.Rect:
    """Screen rect of a square (rank 5 at the top)."""
    return pygame.Rect(sq % FILES * SQUARE, (RANKS - 1 - sq // FILES) * SQUARE, SQUARE, SQUARE)


def button_rects() -> dict[str, pygame.Rect]:
    """Panel button rects by name."""
    x = BOARD_W
    return {"w<": pygame.Rect(x + 168, 14, 34, 32), "w>": pygame.Rect(x + 208, 14, 34, 32),
            "b<": pygame.Rect(x + 168, 54, 34, 32), "b>": pygame.Rect(x + 208, 54, 34, 32),
            "new": pygame.Rect(x + 20, 98, 200, 34)}


def draw_piece(screen: pygame.Surface, font: pygame.font.Font, small: pygame.font.Font, color: int,
               piece: int, rect: pygame.Rect, use_glyphs: bool) -> None:
    """Draw a piece as a glyph or a lettered disc."""
    if use_glyphs:
        img = font.render(GLYPHS[(color, piece)], True, "#111111" if color == BLACK else "#FFFFFF")
        screen.blit(img, img.get_rect(center=rect.center))
    else:
        fill, ink = ("#FFFFFF", "#111111") if color == WHITE else ("#222222", "#FFFFFF")
        pygame.draw.circle(screen, fill, rect.center, 34)
        pygame.draw.circle(screen, "#777777", rect.center, 34, 2)
        img = small.render(LETTERS[piece], True, ink)
        screen.blit(img, img.get_rect(center=rect.center))


def draw(screen: pygame.Surface, game: Game, fonts: tuple, use_glyphs: bool) -> None:
    """Draw the board and side panel."""
    piece_font, label_font, text_font = fonts
    screen.fill(PANEL_BG)
    targets = {m.to for m in game.board.legal_moves() if m.frm == game.selected}
    for sq in range(FILES * RANKS):
        rect = square_rect(sq)
        light = (sq % FILES + sq // FILES) % 2 == 1
        pygame.draw.rect(screen, HIGHLIGHT if sq == game.selected else LIGHT if light else DARK, rect)
        piece = game.board.piece_at(sq)
        if piece:
            draw_piece(screen, piece_font, text_font, piece[0], piece[1], rect, use_glyphs)
        if sq in targets:
            if piece:
                pygame.draw.circle(screen, HIGHLIGHT, rect.center, 46, 6)
            else:
                pygame.draw.circle(screen, HIGHLIGHT, rect.center, 14)
        ink = DARK if light else LIGHT
        if sq // FILES == 0:
            screen.blit(label_font.render(square_name(sq)[0], True, ink), (rect.right - 14, rect.bottom - 18))
        if sq % FILES == 0:
            screen.blit(label_font.render(square_name(sq)[1], True, ink), (rect.x + 4, rect.y + 2))
    x = BOARD_W + 20
    for color, label in ((WHITE, "White"), (BLACK, "Black")):
        y = 20 + 40 * color
        screen.blit(text_font.render(f"{label}: {game.names[color]}", True, TEXT), (x, y))
    for key, rect in button_rects().items():
        pygame.draw.rect(screen, BUTTON, rect, border_radius=4)
        caption = {"new": "New game"}.get(key, key[1])
        img = text_font.render(caption, True, TEXT)
        screen.blit(img, img.get_rect(center=rect.center))
    screen.blit(text_font.render(game.status(), True, "#F5C542"), (x, 150))
    first = max(0, len(game.moves) - MOVES_SHOWN)
    for i, text in enumerate(game.moves[first:]):
        screen.blit(text_font.render(f"{first + i + 1}. {text}", True, TEXT), (x, 185 + 24 * i))


def handle_click(game: Game, pos: tuple[int, int]) -> None:
    """Handle a left click on a button or square."""
    for key, rect in button_rects().items():
        if rect.collidepoint(pos):
            if key == "new":
                game.new_game()
            else:
                game.cycle(WHITE if key[0] == "w" else BLACK, -1 if key[1] == "<" else 1)
            return
    human_turn = game.bots[game.board.turn] is None
    if pos[0] < BOARD_W and human_turn and game.board.game_over_reason() is None:
        game.click_square(next(sq for sq in range(FILES * RANKS) if square_rect(sq).collidepoint(pos)))


def main(max_frames: int | None = None, white: str = "human", black: str = "minimax3") -> None:
    """Run the window until closed (or max_frames)."""
    pygame.init()
    screen = pygame.display.set_mode((BOARD_W + PANEL_W, BOARD_H))
    pygame.display.set_caption("Minichess 4x5")
    piece_font = pygame.font.SysFont("applesymbols,segoeuisymbol,dejavusans,arialunicodems", 72)
    use_glyphs = all(piece_font.metrics(g)[0] is not None for g in GLYPHS.values())
    fonts = (piece_font, pygame.font.SysFont(None, 20), pygame.font.SysFont(None, 24))
    game = Game(white, black)
    clock = pygame.time.Clock()
    frames, running = 0, True
    while running and (max_frames is None or frames < max_frames):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                handle_click(game, event.pos)
        draw(screen, game, fonts, use_glyphs)
        pygame.display.flip()
        bot = game.bots[game.board.turn]
        if bot and game.board.game_over_reason() is None:
            move = bot.get_move(game.board)
            if move:
                game.play(move)
            pygame.time.wait(250)
        clock.tick(30)
        frames += 1
    pygame.quit()


if __name__ == "__main__":
    main()
