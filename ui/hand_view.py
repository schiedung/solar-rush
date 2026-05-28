import pygame

from game.card import Card
from game.state import GameState
import ui.colors as C
import ui.fonts as F
import ui.layout as L


def _draw_card(
    surf: pygame.Surface,
    card: Card,
    rect: pygame.Rect,
    hovered: bool,
    selected: bool,
) -> None:
    area_color = C.AREA.get(card.area, C.CELL_BORDER)
    area_dark  = C.AREA_DARK.get(card.area, C.CELL_BG)

    bg = C.BTN_HOVER if hovered else C.CELL_BG
    border = area_color if selected else (C.CELL_BORDER if not hovered else area_color)
    border_w = 3 if selected else (2 if hovered else 1)

    pygame.draw.rect(surf, bg, rect, border_radius=7)
    pygame.draw.rect(surf, border, rect, border_w, border_radius=7)

    band = pygame.Rect(rect.x + border_w, rect.y + border_w, rect.width - 2 * border_w, 22)
    pygame.draw.rect(surf, area_dark, band)
    area_lbl = F.get('tiny').render(C.AREA_LABEL.get(card.area, card.area), True, area_color)
    surf.blit(area_lbl, (band.x + 4, band.y + 4))

    tier_txt = '★' * card.tier + '☆' * (3 - card.tier)
    tier_surf = F.get('tiny').render(tier_txt, True, C.TEXT_GOLD)
    surf.blit(tier_surf, (band.right - tier_surf.get_width() - 4, band.y + 4))

    name_y = rect.y + 28
    _blit_wrapped(surf, card.name, F.get('bold'), C.TEXT_MAIN, rect.x + 5, name_y, rect.width - 10, 2)

    desc_y = rect.y + 66
    _blit_wrapped(surf, card.description, F.get('tiny'), C.TEXT_DIM, rect.x + 5, desc_y, rect.width - 10, 4)

    etype = card.effect.get('type', '')
    if etype.startswith('event_'):
        badge = F.get('tiny').render('EVENT', True, C.TEXT_RED)
    elif etype == 'farm_multiplier':
        delta = card.effect.get('delta', 0)
        badge = F.get('tiny').render(f'+{int(delta*100)}% FARM', True, C.TEXT_GOLD)
    else:
        delta = card.effect.get('delta', 1)
        badge = F.get('tiny').render(f'+{delta} tier', True, C.CYAN)
    surf.blit(badge, (rect.centerx - badge.get_width() // 2, rect.bottom - 18))


def _blit_wrapped(
    surf: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple,
    x: int, y: int, max_w: int, max_lines: int,
) -> None:
    words = text.split()
    lines: list[str] = []
    line = ''
    for word in words:
        test = (line + ' ' + word).strip()
        if font.size(test)[0] <= max_w:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
        if len(lines) >= max_lines:
            break
    if line and len(lines) < max_lines:
        lines.append(line)
    lh = font.get_height() + 2
    for i, ln in enumerate(lines[:max_lines]):
        surf.blit(font.render(ln, True, color), (x, y + i * lh))


def draw(
    surf: pygame.Surface,
    state: GameState,
    mouse_pos: tuple[int, int],
) -> list[pygame.Rect]:
    """Draw the current player's hand. Returns card rects in hand order."""
    pygame.draw.rect(surf, C.HAND_BG,
                     (0, L.TOPBAR_H + L.MAIN_H, L.SW, L.HAND_H))
    pygame.draw.line(surf, C.DIVIDER,
                     (0, L.TOPBAR_H + L.MAIN_H),
                     (L.SW, L.TOPBAR_H + L.MAIN_H), 2)

    hand = state.current_player.hand
    selected_card = state.selected_card

    card_rects: list[pygame.Rect] = []
    for i, card in enumerate(hand):
        rect = L.hand_rect(i, len(hand))
        hovered = rect.collidepoint(mouse_pos)
        selected = card is selected_card
        _draw_card(surf, card, rect, hovered, selected)
        card_rects.append(rect)

    hand_lbl = F.get('tiny').render(
        f'Hand  ({len(hand)} cards)  —  slot cards are free; Draw / Build cost actions',
        True, C.TEXT_DIM,
    )
    surf.blit(hand_lbl, (8, L.TOPBAR_H + L.MAIN_H + 4))

    return card_rects
