import pygame

from game.card import Card
from game.state import GameState
import ui.colors as C
import ui.fonts as F
import ui.layout as L
import ui.assets as A


def _card_badge(card: Card) -> str:
    etype = card.effect.get('type', '')
    if card.is_slot_card():
        return f"×{_slot_multiplier(card):.2f}"
    if etype == 'farm_multiplier':
        return f"×{1.0 + card.effect.get('delta', 0):.2f}"
    if etype == 'event_policy_subsidy':
        return '+2 CARDS'
    if etype.startswith('event_'):
        return 'EVENT'
    return ''


def _slot_multiplier(card: Card) -> float:
    tier = card.effect.get('to_tier', 0)
    if card.area == 'material_science':
        return {1: 1.30, 2: 1.60, 3: 2.00, 4: 2.80}.get(tier, 1.00)
    if card.area == 'chemistry':
        return {1: 1.15, 2: 1.30, 3: 1.45, 4: 1.65}.get(tier, 1.00)
    if card.area == 'physics':
        return {1: 1.20, 2: 1.40, 3: 1.60, 4: 1.90}.get(tier, 1.00)
    return 1.00


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

    badge_txt = _card_badge(card)
    badge_top = F.get('bold').render(badge_txt, True, C.WHITE)
    surf.blit(badge_top, (band.right - badge_top.get_width() - 4, band.y + 2))

    name_y = rect.y + 28
    _blit_wrapped(surf, card.name, F.get('bold'), C.TEXT_MAIN, rect.x + 5, name_y, rect.width - 10, 2)

    art_rect = pygame.Rect(rect.x + 6, rect.y + 58, rect.width - 12, 48)
    art = A.get_card_image(card.id, art_rect.width, art_rect.height)
    surf.blit(art, art_rect)
    pygame.draw.rect(surf, area_color, art_rect, 1, border_radius=4)

    desc_y = rect.y + 111
    _blit_wrapped(surf, card.description, F.get('tiny'), C.TEXT_DIM, rect.x + 5, desc_y, rect.width - 10, 2)

    badge = F.get('bold').render(badge_txt, True, C.WHITE)
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
) -> dict:
    """Draw the current player's hand. Returns dict with 'rects' and 'hovered_card'."""
    hand = state.current_player.hand
    selected_card = state.selected_card

    card_rects: list[pygame.Rect] = []
    hovered_card = None
    for i, card in enumerate(hand):
        rect = L.hand_rect(i, len(hand))
        hovered = rect.collidepoint(mouse_pos)
        selected = card is selected_card
        _draw_card(surf, card, rect, hovered, selected)
        card_rects.append(rect)
        if hovered:
            hovered_card = card

    hand_lbl = F.get('tiny').render(
        f'Hand  ({len(hand)} cards)  —  slot cards are free; Draw / Build cost actions',
        True, C.TEXT_DIM,
    )
    surf.blit(hand_lbl, (L.HAND_PANEL_X + 8, L.TOPBAR_H + L.MAIN_H + 4))

    return {'rects': card_rects, 'hovered_card': hovered_card}
