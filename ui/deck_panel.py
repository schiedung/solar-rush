import pygame

from game.state import GameState, Phase
import ui.colors as C
import ui.fonts as F
import ui.layout as L
import ui.assets as A

_AREAS = ('material_science', 'chemistry', 'physics', 'engineering')


def _draw_button(
    surf: pygame.Surface,
    rect: pygame.Rect,
    area: str,
    deck_len: int,
    discard_len: int,
    mouse_pos: tuple[int, int],
    available: bool,
    research_mode: bool,
) -> None:
    hovered = rect.collidepoint(mouse_pos) and available
    bg = C.BTN_HOVER if hovered else (C.BTN_NORMAL if available else C.BTN_DISABLED)
    border = C.AREA.get(area, C.BTN_BORDER) if available else C.DIVIDER

    pygame.draw.rect(surf, bg, rect, border_radius=8)
    pygame.draw.rect(surf, border, rect, 2, border_radius=8)

    pygame.draw.rect(surf, C.AREA.get(area, C.BTN_BORDER),
                     (rect.x, rect.y, 6, rect.height), border_radius=4)

    card_back = A.get('card_back', 34, 48)
    stack_x = rect.right - 46
    stack_y = rect.y + 22
    for offset in (8, 4, 0):
        back_rect = pygame.Rect(stack_x - offset, stack_y - offset, 34, 48)
        surf.blit(card_back, back_rect)
        pygame.draw.rect(surf, border, back_rect, 1, border_radius=4)

    name_txt = C.AREA_LABEL.get(area, area)
    name_surf = F.get('bold').render(name_txt, True, C.TEXT_MAIN if available else C.TEXT_DIM)
    surf.blit(name_surf, (rect.x + 14, rect.y + 8))

    count_surf = F.get('small').render(f'{deck_len} cards', True, C.TEXT_DIM)
    surf.blit(count_surf, (rect.x + 14, rect.y + 30))

    if research_mode:
        tag = F.get('tiny').render('RESEARCH ×2', True, C.TEXT_GOLD)
        surf.blit(tag, (rect.x + 14, rect.y + 50))
    elif not available:
        tag = F.get('tiny').render('BLOCKED', True, C.TEXT_RED)
        surf.blit(tag, (rect.x + 14, rect.y + 50))

    hint = F.get('tiny').render('DRAW', True, C.TEXT_DIM)
    surf.blit(hint, (stack_x + 17 - hint.get_width() // 2, rect.y + 6))


def draw(
    surf: pygame.Surface,
    state: GameState,
    mouse_pos: tuple[int, int],
) -> None:
    p = state.current_player
    phase = state.phase
    research_mode = phase == Phase.RESEARCH_PICK_AREA
    draw_mode = phase in (Phase.ACTION, Phase.RESEARCH_PICK_AREA)

    for area in _AREAS:
        rect = L.DECK_RECTS[area]
        deck = state.decks[area]
        available = (
            draw_mode
            and area not in p.blocked_areas
            and len(deck) > 0
        )
        if research_mode:
            available = available and state.actions_remaining >= 2
        _draw_button(surf, rect, area,
                     len(deck), len(deck.discard_pile),
                     mouse_pos, available, research_mode)

    can_act = phase == Phase.ACTION and state.actions_remaining > 0
    can_build = can_act and not p.block_build

    _draw_action_btn(surf, L.BUILD_BTN, 'Build Cell',
                     can_build, mouse_pos, C.BTN_CONFIRM)
    _draw_action_btn(surf, L.RESEARCH_BTN,
                     'Research',
                     can_act and state.actions_remaining >= 2, mouse_pos)
    _draw_action_btn(surf, L.PASS_BTN, 'Pass Action',
                     can_act, mouse_pos)
    _draw_action_btn(surf, L.FINISH_TURN_BTN, 'Finish Turn',
                     phase == Phase.ACTION, mouse_pos, C.BTN_CONFIRM)

    status = _status_text(state)
    st = F.get('small').render(status, True, C.TEXT_DIM)
    _blit_clipped(surf, st, pygame.Rect(L.ACTION_X, L.STATUS_TEXT_Y, 310, st.get_height()))

    # Score board — current output (kW)
    y = L.SCOREBOARD_Y
    for i, player in enumerate(state.players):
        highlight = i == state.current_player_idx
        color = player.color if highlight else C.TEXT_DIM
        arrow = '► ' if highlight else '  '
        line = F.get('body').render(
            f'{arrow}{player.name}: {player.total_output():.2f} kW', True, color
        )
        _blit_clipped(surf, line, pygame.Rect(L.ACTION_X, y + i * 19, 310, line.get_height()))

    _draw_keybindings(surf)


def _draw_action_btn(
    surf: pygame.Surface,
    rect: pygame.Rect,
    label: str,
    enabled: bool,
    mouse_pos: tuple[int, int],
    border_color: tuple = None,
) -> None:
    hovered = rect.collidepoint(mouse_pos) and enabled
    bg = C.BTN_HOVER if hovered else (C.BTN_NORMAL if enabled else C.BTN_DISABLED)
    bc = border_color if (border_color and enabled) else (C.BTN_BORDER if enabled else C.DIVIDER)

    pygame.draw.rect(surf, bg, rect, border_radius=6)
    pygame.draw.rect(surf, bc, rect, 2, border_radius=6)

    lbl = F.get('bold').render(label, True, C.TEXT_MAIN if enabled else C.TEXT_DIM)
    surf.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                    rect.centery - lbl.get_height() // 2))


def _blit_clipped(surf: pygame.Surface, text_surf: pygame.Surface, rect: pygame.Rect) -> None:
    surf.blit(text_surf, rect.topleft, area=pygame.Rect(0, 0, rect.width, rect.height))


def _draw_keybindings(surf: pygame.Surface) -> None:
    x = L.HAND_PANEL_X + L.HAND_PANEL_W + 10  # always right of hand cards
    y = L.SH - 58
    for text in ('ESC / RMB — deselect', 'Ctrl+F  fullscreen   Ctrl+Q  quit'):
        s = F.get('tiny').render(text, True, C.TEXT_DIM)
        surf.blit(s, (x, y))
        y += s.get_height() + 3


def _status_text(state: GameState) -> str:
    phase = state.phase
    p = state.current_player
    if phase == Phase.ACTION:
        if p.block_build:
            return f'Actions: {state.actions_remaining}  |  Grid Failure — Build blocked!'
        if state.actions_remaining <= 0:
            return 'No actions left — swap prototype cards or Finish Turn'
        return f'Actions remaining: {state.actions_remaining}  |  Click a card, deck, or button'
    if phase == Phase.TARGETING_PLAYER:
        return f'Select a target player for: {state.selected_card.name}'
    if phase == Phase.RESEARCH_PICK_AREA:
        return 'Research: select a deck to peek 3 cards'
    if phase == Phase.RESEARCH_CHOOSE:
        return 'Research: click a card to keep it'
    if phase == Phase.HANDOFF:
        return 'Turn complete — click Finish Turn to pass'
    return ''
