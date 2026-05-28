import sys
import pygame

from game.state import make_game, Phase
from game.engine import TurnEngine
import ui.fonts as F
import ui.assets as A
import ui.renderer as R
import ui.layout as L

TITLE = 'Solar Rush — Research & Build'
FPS = 60
LOGICAL_W, LOGICAL_H = L.SW, L.SH

_fullscreen = False


def _toggle_fullscreen(screen: pygame.Surface) -> pygame.Surface:
    global _fullscreen
    _fullscreen = not _fullscreen
    if _fullscreen:
        return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    return pygame.display.set_mode((LOGICAL_W, LOGICAL_H), pygame.RESIZABLE)


def _scale_mouse(pos: tuple[int, int], screen: pygame.Surface) -> tuple[int, int]:
    sw, sh = screen.get_size()
    return (int(pos[0] * LOGICAL_W / sw), int(pos[1] * LOGICAL_H / sh))


def reset_game(num_players: int):
    state = make_game(num_players)
    engine = TurnEngine(state)
    engine.begin_turn()
    return state, engine


def handle_click(
    pos: tuple[int, int],
    state,
    engine: TurnEngine,
    rects: R.UIRects,
) -> str | None:
    phase = state.phase

    if phase == Phase.ACTION:
        # Unslot buttons on prototype slots (free, no action cost)
        for slot_key, ubtn in rects.slot_rects.items():
            if ubtn.collidepoint(pos):
                engine.perform_unslot(slot_key)
                return
        # Finish Turn button
        if L.FINISH_TURN_BTN.collidepoint(pos):
            engine.finish_turn()
            return
        # Deck draw buttons
        for area, rect in L.DECK_RECTS.items():
            if rect.collidepoint(pos):
                engine.perform_draw(area)
                return
        # Action buttons
        if L.BUILD_BTN.collidepoint(pos):
            engine.perform_build()
            return
        if L.RESEARCH_BTN.collidepoint(pos):
            engine.enter_research_mode()
            return
        if L.PASS_BTN.collidepoint(pos):
            engine.perform_pass()
            return
        # Hand cards
        hand = state.current_player.hand
        for i, rect in enumerate(rects.hand_rects):
            if rect.collidepoint(pos) and i < len(hand):
                engine.select_card(hand[i])
                return

    elif phase == Phase.RESEARCH_PICK_AREA:
        for area, rect in L.DECK_RECTS.items():
            if rect.collidepoint(pos):
                engine.start_research(area)
                return

    elif phase == Phase.TARGETING_PLAYER:
        for i, rect in enumerate(rects.player_target_rects):
            if rect.collidepoint(pos):
                if engine.perform_play_event(i):
                    return

    elif phase == Phase.RESEARCH_CHOOSE:
        for i, rect in enumerate(rects.research_rects):
            if rect.collidepoint(pos):
                engine.complete_research(i)
                return

    elif phase == Phase.HANDOFF:
        if rects.handoff_btn.collidepoint(pos):
            engine.advance_to_next_player()

    elif phase == Phase.GAME_OVER:
        if rects.play_again_btn.collidepoint(pos):
            return 'reset'


def _player_count_screen(
    logical: pygame.Surface,
    screen: pygame.Surface,
    clock: pygame.time.Clock,
) -> int:
    import ui.colors as C
    btns = {
        2: pygame.Rect(LOGICAL_W // 2 - 180, LOGICAL_H // 2 - 30, 100, 60),
        3: pygame.Rect(LOGICAL_W // 2 - 50,  LOGICAL_H // 2 - 30, 100, 60),
        4: pygame.Rect(LOGICAL_W // 2 + 80,  LOGICAL_H // 2 - 30, 100, 60),
    }
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f and (event.mod & pygame.KMOD_CTRL):
                    screen = _toggle_fullscreen(screen)
                elif event.key == pygame.K_q and (event.mod & pygame.KMOD_CTRL):
                    pygame.quit()
                    sys.exit(0)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                lpos = _scale_mouse(event.pos, screen)
                for n, rect in btns.items():
                    if rect.collidepoint(lpos):
                        return n

        mouse = _scale_mouse(pygame.mouse.get_pos(), screen)

        logical.blit(A.get('background', LOGICAL_W, LOGICAL_H), (0, 0))
        shade = pygame.Surface((LOGICAL_W, LOGICAL_H), pygame.SRCALPHA)
        shade.fill((*C.BG, 155))
        logical.blit(shade, (0, 0))

        logo = A.get('logo', 420, 218)
        logical.blit(logo, (LOGICAL_W // 2 - logo.get_width() // 2, LOGICAL_H // 2 - 245))

        sub = F.get('large').render('How many players?', True, C.TEXT_MAIN)
        logical.blit(sub, (LOGICAL_W // 2 - sub.get_width() // 2, LOGICAL_H // 2 - 75))

        hint = F.get('small').render(
            'Research cards  ·  Upgrade your prototype  ·  Build units  ·  Reach 20 kW first',
            True, C.TEXT_DIM,
        )
        logical.blit(hint, (LOGICAL_W // 2 - hint.get_width() // 2, LOGICAL_H // 2 + 60))

        for n, rect in btns.items():
            hov = rect.collidepoint(mouse)
            pygame.draw.rect(logical, C.BTN_HOVER if hov else C.BTN_NORMAL, rect, border_radius=10)
            pygame.draw.rect(logical, C.TEXT_GOLD, rect, 2, border_radius=10)
            lbl = F.get('title').render(str(n), True, C.TEXT_GOLD)
            logical.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                                rect.centery - lbl.get_height() // 2))

        pygame.transform.scale(logical, screen.get_size(), screen)
        pygame.display.flip()
        clock.tick(FPS)


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((LOGICAL_W, LOGICAL_H), pygame.RESIZABLE)
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    F.load()
    A.load()

    logical = pygame.Surface((LOGICAL_W, LOGICAL_H))

    num_players = _player_count_screen(logical, screen, clock)
    state, engine = reset_game(num_players)
    rects = R.UIRects()

    while True:
        mouse_pos = _scale_mouse(pygame.mouse.get_pos(), screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    engine.deselect_card()
                elif event.key == pygame.K_f and (event.mod & pygame.KMOD_CTRL):
                    screen = _toggle_fullscreen(screen)
                elif event.key == pygame.K_q and (event.mod & pygame.KMOD_CTRL):
                    pygame.quit()
                    sys.exit(0)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                lpos = _scale_mouse(event.pos, screen)
                if event.button == 1:
                    result = handle_click(lpos, state, engine, rects)
                    if result == 'reset':
                        num_players = _player_count_screen(logical, screen, clock)
                        state, engine = reset_game(num_players)
                elif event.button == 3:
                    engine.deselect_card()

        rects = R.draw(logical, state, mouse_pos)
        pygame.transform.scale(logical, screen.get_size(), screen)
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == '__main__':
    main()
