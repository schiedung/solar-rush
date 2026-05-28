import sys
import pygame

from game.state import make_game, Phase
from game.engine import TurnEngine
import ui.fonts as F
import ui.assets as A
import ui.renderer as R
import ui.layout as L

TITLE = 'Solar Farm — Research & Build'
FPS = 60


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
        # Hand cards (slot or event select)
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

    elif phase == Phase.DISCARD:
        hand = state.current_player.hand
        for i, rect in enumerate(rects.hand_rects):
            if rect.collidepoint(pos) and i < len(hand):
                engine.perform_discard(i)
                return

    elif phase == Phase.HANDOFF:
        if rects.handoff_btn.collidepoint(pos):
            engine.advance_to_next_player()

    elif phase == Phase.GAME_OVER:
        if rects.play_again_btn.collidepoint(pos):
            return 'reset'


def _player_count_screen(screen: pygame.Surface, clock: pygame.time.Clock) -> int:
    import ui.colors as C
    btns = {
        2: pygame.Rect(L.SW // 2 - 180, L.SH // 2 - 30, 100, 60),
        3: pygame.Rect(L.SW // 2 - 50,  L.SH // 2 - 30, 100, 60),
        4: pygame.Rect(L.SW // 2 + 80,  L.SH // 2 - 30, 100, 60),
    }
    while True:
        mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for n, rect in btns.items():
                    if rect.collidepoint(event.pos):
                        return n

        screen.fill(C.BG)
        title = F.get('title').render('Solar Farm', True, C.TEXT_GOLD)
        screen.blit(title, (L.SW // 2 - title.get_width() // 2, L.SH // 2 - 130))

        sub = F.get('large').render('How many players?', True, C.TEXT_MAIN)
        screen.blit(sub, (L.SW // 2 - sub.get_width() // 2, L.SH // 2 - 75))

        hint = F.get('small').render(
            'Research cards  ·  Upgrade your prototype  ·  Build units  ·  Bank kWh',
            True, C.TEXT_DIM,
        )
        screen.blit(hint, (L.SW // 2 - hint.get_width() // 2, L.SH // 2 + 60))

        for n, rect in btns.items():
            hov = rect.collidepoint(mouse)
            pygame.draw.rect(screen, (55, 80, 130) if hov else (35, 55, 95), rect, border_radius=10)
            pygame.draw.rect(screen, C.TEXT_GOLD, rect, 2, border_radius=10)
            lbl = F.get('title').render(str(n), True, C.TEXT_GOLD)
            screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                               rect.centery - lbl.get_height() // 2))

        pygame.display.flip()
        clock.tick(FPS)


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((L.SW, L.SH))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    F.load()
    A.load()

    num_players = _player_count_screen(screen, clock)
    state, engine = reset_game(num_players)
    rects = R.UIRects()
    mouse_pos = (0, 0)

    while True:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    engine.deselect_card()
                elif event.key == pygame.K_F4 and (event.mod & pygame.KMOD_ALT):
                    pygame.quit()
                    sys.exit(0)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    result = handle_click(event.pos, state, engine, rects)
                    if result == 'reset':
                        num_players = _player_count_screen(screen, clock)
                        state, engine = reset_game(num_players)
                elif event.button == 3:
                    engine.deselect_card()

        rects = R.draw(screen, state, mouse_pos)
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == '__main__':
    main()
