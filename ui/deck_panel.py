import pygame

from game.state import GameState, Phase
import ui.colors as C
import ui.fonts as F
import ui.layout as L

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

    # Area color accent bar on left
    pygame.draw.rect(surf, C.AREA.get(area, C.BTN_BORDER),
                     (rect.x, rect.y, 6, rect.height), border_radius=4)

    name_txt = C.AREA_LABEL.get(area, area)
    name_surf = F.get('bold').render(name_txt, True, C.TEXT_MAIN if available else C.TEXT_DIM)
    surf.blit(name_surf, (rect.x + 14, rect.y + 8))

    count_surf = F.get('small').render(f'{deck_len} cards', True, C.TEXT_DIM)
    surf.blit(count_surf, (rect.x + 14, rect.y + 28))

    if research_mode:
        tag = F.get('tiny').render('RESEARCH ×2', True, C.TEXT_GOLD)
        surf.blit(tag, (rect.x + 14, rect.y + 46))
    elif not available:
        tag = F.get('tiny').render('BLOCKED', True, C.TEXT_RED)
        surf.blit(tag, (rect.x + 14, rect.y + 46))

    # Draw icon hint on right
    hint = F.get('tiny').render('DRAW', True, C.TEXT_DIM if available else C.TEXT_DIM)
    surf.blit(hint, (rect.right - hint.get_width() - 10, rect.y + 8))


def draw(
    surf: pygame.Surface,
    state: GameState,
    mouse_pos: tuple[int, int],
) -> None:
    """Draw the right panel: deck buttons + action buttons."""
    # Panel background
    pygame.draw.rect(surf, C.PANEL_BG,
                     (L.FARM_W, L.TOPBAR_H, L.PANEL_W, L.MAIN_H))

    p = state.current_player
    phase = state.phase
    research_mode = phase == Phase.RESEARCH_PICK_AREA
    draw_mode = phase in (Phase.ACTION, Phase.RESEARCH_PICK_AREA)

    # ── Deck buttons ────────────────────────────────────────────────────────
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

    # ── Action buttons ───────────────────────────────────────────────────────
    can_act = phase == Phase.ACTION and state.actions_remaining > 0

    _draw_action_btn(surf, L.BUILD_BTN, 'Build Cell',
                     can_act, mouse_pos, C.BTN_CONFIRM)
    _draw_action_btn(surf, L.RESEARCH_BTN,
                     f'Research  (costs 2)',
                     can_act and state.actions_remaining >= 2, mouse_pos)
    _draw_action_btn(surf, L.PASS_BTN, 'Pass Action',
                     can_act, mouse_pos)

    # Status line
    status = _status_text(state)
    st = F.get('small').render(status, True, C.TEXT_DIM)
    surf.blit(st, (L.ACTION_X, L.STATUS_TEXT_Y))

    # kWh scoreboard (below action buttons)
    y = L.SCOREBOARD_Y
    for i, player in enumerate(state.players):
        highlight = i == state.current_player_idx
        color = player.color if highlight else C.TEXT_DIM
        arrow = '► ' if highlight else '  '
        line = F.get('body').render(
            f'{arrow}{player.name}: {player.banked_kwh:.1f} kWh', True, color
        )
        surf.blit(line, (L.ACTION_X, y + i * 19))


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


def _status_text(state: GameState) -> str:
    phase = state.phase
    p = state.current_player
    if phase == Phase.ACTION:
        return f'Actions remaining: {state.actions_remaining}  |  Click a card, deck, or button'
    if phase == Phase.TARGETING_CELL:
        return f'Select a cell to upgrade with: {state.selected_card.name}'
    if phase == Phase.TARGETING_PLAYER:
        return f'Select a target player for: {state.selected_card.name}'
    if phase == Phase.RESEARCH_PICK_AREA:
        return 'Research: select a deck to peek 3 cards'
    if phase == Phase.RESEARCH_CHOOSE:
        return 'Research: click a card to keep it'
    if phase == Phase.DISCARD:
        discard_n = len(p.hand) - p.HAND_LIMIT
        return f'Discard {discard_n} card(s) — click cards to discard'
    if phase == Phase.SCORE:
        return 'Scoring...'
    return ''
