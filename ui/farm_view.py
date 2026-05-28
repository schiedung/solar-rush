import pygame

from game.cell import JUNCTION_TIERS, OPTICAL_TIERS, CONTACT_TIERS
from game.state import GameState, Phase
import ui.colors as C
import ui.fonts as F
import ui.layout as L

# ── Prototype panel geometry ─────────────────────────────────────────────────
PROTO_X      = 34
PROTO_Y      = L.TOPBAR_H + 20
PROTO_W      = 342
PROTO_H      = 336
SLOT_Y       = PROTO_Y + 48
SLOT_H       = 86
SLOT_W       = PROTO_W
SLOT_GAP     = 8
SLOT_X0      = PROTO_X

SLOT_KEYS    = ('junction', 'optical', 'contact')
SLOT_AREAS   = ('material_science', 'chemistry', 'physics')

# ── Units grid geometry ───────────────────────────────────────────────────────
UNIT_X0      = 420
UNIT_Y0      = L.TOPBAR_H + 270
UNIT_W, UNIT_H = 78, 58
UNIT_GAP     = 8
UNITS_PER_ROW = 6

_UNSLOT_W, _UNSLOT_H = 28, 18


def _unit_color(kwh: float) -> tuple:
    if kwh < 1.5:  return C.TIER_COLORS[0]
    if kwh < 3.0:  return C.TIER_COLORS[1]
    if kwh < 5.0:  return C.TIER_COLORS[2]
    if kwh < 7.0:  return C.TIER_COLORS[3]
    return C.TIER_COLORS[4]


def _slot_rect(k: int) -> pygame.Rect:
    y = SLOT_Y + k * (SLOT_H + SLOT_GAP)
    return pygame.Rect(SLOT_X0, y, SLOT_W, SLOT_H)


def _unslot_rect(slot_rect: pygame.Rect) -> pygame.Rect:
    return pygame.Rect(
        slot_rect.right - _UNSLOT_W - 4,
        slot_rect.y + 4,
        _UNSLOT_W, _UNSLOT_H,
    )


def _unit_rect(idx: int) -> pygame.Rect:
    row, col = divmod(idx, UNITS_PER_ROW)
    x = UNIT_X0 + col * (UNIT_W + UNIT_GAP)
    y = UNIT_Y0 + row * (UNIT_H + UNIT_GAP)
    return pygame.Rect(x, y, UNIT_W, UNIT_H)


def _draw_slot(
    surf: pygame.Surface,
    rect: pygame.Rect,
    slot_key: str,
    area: str,
    card,
    tier_data: list,
    mouse_pos: tuple,
) -> tuple:
    """Draw one prototype slot. Returns (unslot_btn_rect_or_None, is_hovered_on_card)."""
    area_color = C.AREA.get(area, C.CELL_BORDER)
    area_dark  = C.AREA_DARK.get(area, C.CELL_BG)
    area_label = C.AREA_LABEL.get(area, area)

    has_card = card is not None
    is_hovered = has_card and rect.collidepoint(mouse_pos)
    bg = area_dark if has_card else C.CELL_BG
    border = area_color if has_card else (40, 55, 90)
    if is_hovered:
        border = C.WHITE
    border_w = 2 if has_card else 1

    pygame.draw.rect(surf, bg, rect, border_radius=8)
    pygame.draw.rect(surf, border, rect, border_w, border_radius=8)

    accent = pygame.Rect(rect.x + border_w, rect.y + border_w, rect.width - 2*border_w, 20)
    pygame.draw.rect(surf, area_dark if not has_card else area_color, accent)

    a_lbl = F.get('tiny').render(area_label, True, C.WHITE if has_card else C.TEXT_DIM)
    surf.blit(a_lbl, (accent.x + 4, accent.y + 3))

    unslot_btn = None

    if has_card:
        tier = card.effect['to_tier']
        mult = tier_data[tier]['multiplier']

        content_y = rect.y + 30

        name_surf = F.get('bold').render(card.name[:20], True, C.TEXT_MAIN)
        surf.blit(name_surf, (rect.x + 8, content_y))

        mult_surf = F.get('large').render(f'×{mult:.2f}', True, C.WHITE)
        surf.blit(mult_surf, (rect.x + 8, content_y + 26))

        # Unslot button
        ubtn = _unslot_rect(rect)
        hov = ubtn.collidepoint(mouse_pos)
        pygame.draw.rect(surf, C.BTN_HOVER if hov else C.BTN_NORMAL, ubtn, border_radius=4)
        pygame.draw.rect(surf, C.TEXT_DIM, ubtn, 1, border_radius=4)
        lbl = F.get('tiny').render('↩', True, C.TEXT_MAIN)
        surf.blit(lbl, (ubtn.centerx - lbl.get_width() // 2,
                        ubtn.centery - lbl.get_height() // 2))
        unslot_btn = ubtn
    else:
        empty = F.get('small').render('[ EMPTY ]', True, (60, 80, 120))
        surf.blit(empty, (rect.centerx - empty.get_width() // 2, rect.centery + 4))
        hint = F.get('tiny').render(f'Play a {area_label} card', True, (50, 65, 100))
        surf.blit(hint, (rect.centerx - hint.get_width() // 2, rect.centery + 26))

    return (unslot_btn, is_hovered)


def draw(surf: pygame.Surface, state: GameState, mouse_pos: tuple) -> dict:
    """Draw the current player's prototype panel and built-units grid.
    Returns dict with 'unslot_rects' and 'hovered_card'."""
    p = state.current_player
    proto = p.prototype

    proto_bg = pygame.Rect(PROTO_X, PROTO_Y, PROTO_W, PROTO_H)

    kwh_out = proto.kwh_output()
    title = F.get('bold').render(
        f'PROTOTYPE  —  Next unit value: {kwh_out:.3f} kW',
        True, C.TEXT_GOLD,
    )
    surf.blit(title, (proto_bg.x + 10, proto_bg.y + 12))

    tier_data_map = {
        'junction': JUNCTION_TIERS,
        'optical':  OPTICAL_TIERS,
        'contact':  CONTACT_TIERS,
    }
    cards = (proto.junction_card, proto.optical_card, proto.contact_card)
    slot_rects: dict[str, pygame.Rect] = {}
    hovered_card = None
    for k, (slot_key, area, card) in enumerate(zip(SLOT_KEYS, SLOT_AREAS, cards)):
        ubtn, slot_hovered = _draw_slot(surf, _slot_rect(k), slot_key, area, card,
                          tier_data_map[slot_key], mouse_pos)
        if ubtn is not None:
            slot_rects[slot_key] = ubtn
        if slot_hovered and card is not None:
            hovered_card = card

    # ── Built units ──────────────────────────────────────────────────────────
    units_label = F.get('body').render(
        f'Built Units: {len(p.units)}   |   '
        f'Output: {p.total_output():.2f} kW   |   '
        f'Bonus: ×{1.0 + p.farm_bonus:.2f}',
        True, C.TEXT_DIM,
    )
    surf.blit(units_label, (UNIT_X0, UNIT_Y0 - 24))

    if not p.units:
        no_units = F.get('body').render('No units built yet — use the Build action!', True, (50, 65, 100))
        surf.blit(no_units, (UNIT_X0, UNIT_Y0 + 10))
    else:
        for i, kwh in enumerate(p.units):
            rect = _unit_rect(i)
            if rect.bottom > L.TOPBAR_H + L.MAIN_H - 2:
                break
            col = _unit_color(kwh)
            dark = tuple(max(0, c - 60) for c in col)
            pygame.draw.rect(surf, dark, rect, border_radius=6)
            pygame.draw.rect(surf, col, rect, 2, border_radius=6)
            val = F.get('bold').render(f'{kwh:.2f}', True, C.TEXT_GOLD)
            surf.blit(val, (rect.centerx - val.get_width() // 2, rect.y + 8))
            lbl = F.get('tiny').render('kW', True, C.TEXT_DIM)
            surf.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.y + 32))

    if p.blocked_areas:
        blocked_txt = 'BLOCKED: ' + ', '.join(
            C.AREA_LABEL.get(a, a) for a in p.blocked_areas if a in C.AREA_LABEL
        )
        b_surf = F.get('tiny').render(blocked_txt, True, C.TEXT_RED)
        surf.blit(b_surf, (UNIT_X0, L.TOPBAR_H + L.MAIN_H - 18))

    if p.block_build:
        bb_surf = F.get('tiny').render('GRID FAILURE — Build blocked this turn', True, C.TEXT_RED)
        surf.blit(bb_surf, (UNIT_X0, L.TOPBAR_H + L.MAIN_H - 34))

    return {'unslot_rects': slot_rects, 'hovered_card': hovered_card}
