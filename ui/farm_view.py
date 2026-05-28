import pygame

from game.cell import JUNCTION_TIERS, OPTICAL_TIERS, CONTACT_TIERS, MAX_TIER, Prototype
from game.state import GameState, Phase
import ui.colors as C
import ui.fonts as F
import ui.layout as L

# ── Prototype panel geometry ─────────────────────────────────────────────────
PROTO_Y      = L.TOPBAR_H + 4
PROTO_H      = 182
SLOT_Y       = PROTO_Y + 32
SLOT_H       = 118
SLOT_W       = 220
SLOT_GAP     = 10
SLOT_X0      = (L.FARM_W - (3 * SLOT_W + 2 * SLOT_GAP)) // 2   # centred in farm

SLOT_KEYS    = ('junction', 'optical', 'contact')
SLOT_AREAS   = ('material_science', 'chemistry', 'physics')

# ── Units grid geometry ───────────────────────────────────────────────────────
UNIT_Y0      = PROTO_Y + PROTO_H + 6
UNIT_W, UNIT_H = 78, 58
UNIT_GAP     = 8
UNITS_PER_ROW = (L.FARM_W - 10) // (UNIT_W + UNIT_GAP)


def _unit_color(kwh: float) -> tuple:
    if kwh < 1.5:  return C.TIER_COLORS[0]
    if kwh < 3.0:  return C.TIER_COLORS[1]
    if kwh < 5.0:  return C.TIER_COLORS[2]
    if kwh < 7.0:  return C.TIER_COLORS[3]
    return C.TIER_COLORS[4]


def _slot_rect(k: int) -> pygame.Rect:
    x = SLOT_X0 + k * (SLOT_W + SLOT_GAP)
    return pygame.Rect(x, SLOT_Y, SLOT_W, SLOT_H)


def _unit_rect(idx: int) -> pygame.Rect:
    row, col = divmod(idx, UNITS_PER_ROW)
    x = 8 + col * (UNIT_W + UNIT_GAP)
    y = UNIT_Y0 + row * (UNIT_H + UNIT_GAP)
    return pygame.Rect(x, y, UNIT_W, UNIT_H)


def _draw_slot(
    surf: pygame.Surface,
    rect: pygame.Rect,
    slot_key: str,
    area: str,
    card,           # Card | None
    tier_data: list,
) -> None:
    area_color = C.AREA.get(area, C.CELL_BORDER)
    area_dark  = C.AREA_DARK.get(area, C.CELL_BG)
    area_label = C.AREA_LABEL.get(area, area)

    has_card = card is not None
    bg = area_dark if has_card else C.CELL_BG
    border = area_color if has_card else (40, 55, 90)
    border_w = 2 if has_card else 1

    pygame.draw.rect(surf, bg, rect, border_radius=8)
    pygame.draw.rect(surf, border, rect, border_w, border_radius=8)

    # Coloured top accent bar
    accent = pygame.Rect(rect.x + border_w, rect.y + border_w, rect.width - 2*border_w, 20)
    pygame.draw.rect(surf, area_dark if not has_card else area_color, accent)

    # Area label
    a_lbl = F.get('tiny').render(area_label, True, C.WHITE if has_card else C.TEXT_DIM)
    surf.blit(a_lbl, (accent.x + 4, accent.y + 3))

    # Slot part label (right of accent)
    slot_lbl = F.get('tiny').render(slot_key.capitalize(), True, C.TEXT_DIM)
    surf.blit(slot_lbl, (accent.right - slot_lbl.get_width() - 4, accent.y + 3))

    if has_card:
        tier = card.effect['to_tier']
        tier_name = tier_data[tier]['name']
        mult = tier_data[tier]['multiplier']

        # Tier bar (visual progress indicator)
        bar_y = rect.y + 28
        bar_rect = pygame.Rect(rect.x + 8, bar_y, rect.width - 16, 8)
        pygame.draw.rect(surf, (30, 40, 70), bar_rect, border_radius=4)
        fill_w = int(bar_rect.width * (tier / MAX_TIER))
        if fill_w > 0:
            fill_rect = pygame.Rect(bar_rect.x, bar_rect.y, fill_w, bar_rect.height)
            pygame.draw.rect(surf, C.TIER_COLORS[tier], fill_rect, border_radius=4)

        # Card name
        name_surf = F.get('bold').render(card.name[:20], True, C.TEXT_MAIN)
        surf.blit(name_surf, (rect.x + 6, bar_y + 14))

        # Tier label
        tier_surf = F.get('small').render(f'Tier {tier}  —  {tier_name}', True, area_color)
        surf.blit(tier_surf, (rect.x + 6, bar_y + 34))

        # Multiplier
        mult_surf = F.get('large').render(f'×{mult:.2f}', True, C.TEXT_GOLD)
        surf.blit(mult_surf, (rect.x + 6, bar_y + 56))

        # Stars
        stars = F.get('tiny').render('★' * tier + '☆' * (MAX_TIER - tier), True, C.TEXT_GOLD)
        surf.blit(stars, (rect.right - stars.get_width() - 6, bar_y + 66))
    else:
        empty = F.get('small').render('[ EMPTY ]', True, (60, 80, 120))
        surf.blit(empty, (rect.centerx - empty.get_width() // 2, rect.centery + 4))
        hint = F.get('tiny').render(f'Play a {area_label} card', True, (50, 65, 100))
        surf.blit(hint, (rect.centerx - hint.get_width() // 2, rect.centery + 26))


def draw(surf: pygame.Surface, state: GameState, mouse_pos: tuple) -> None:
    """Draw the current player's prototype panel and built-units grid."""
    # Farm background
    pygame.draw.rect(surf, C.FARM_BG, (0, L.TOPBAR_H, L.FARM_W, L.MAIN_H))
    pygame.draw.line(surf, C.DIVIDER, (L.FARM_W, L.TOPBAR_H), (L.FARM_W, L.TOPBAR_H + L.MAIN_H), 2)

    p = state.current_player
    proto = p.prototype

    # ── Prototype panel background ───────────────────────────────────────────
    proto_bg = pygame.Rect(4, PROTO_Y, L.FARM_W - 8, PROTO_H)
    pygame.draw.rect(surf, (18, 28, 52), proto_bg, border_radius=10)
    pygame.draw.rect(surf, (45, 65, 110), proto_bg, 1, border_radius=10)

    # Title
    kwh_out = proto.kwh_output()
    title = F.get('bold').render(
        f'PROTOTYPE  —  Next unit value: {kwh_out:.3f} kWh',
        True, C.TEXT_GOLD,
    )
    surf.blit(title, (proto_bg.x + 10, proto_bg.y + 6))

    # Three slots
    tier_data_map = {
        'junction': JUNCTION_TIERS,
        'optical':  OPTICAL_TIERS,
        'contact':  CONTACT_TIERS,
    }
    cards = (proto.junction_card, proto.optical_card, proto.contact_card)
    for k, (slot_key, area, card) in enumerate(zip(SLOT_KEYS, SLOT_AREAS, cards)):
        _draw_slot(surf, _slot_rect(k), slot_key, area, card, tier_data_map[slot_key])

    # ── Built units section ──────────────────────────────────────────────────
    units_label = F.get('body').render(
        f'Built Units: {len(p.units)}   |   '
        f'Output: {p.total_output():.2f} kWh/turn   |   '
        f'Bonus: ×{1.0 + p.farm_bonus:.2f}',
        True, C.TEXT_DIM,
    )
    surf.blit(units_label, (8, UNIT_Y0 - 20))

    if not p.units:
        no_units = F.get('body').render('No units built yet — use the Build action!', True, (50, 65, 100))
        surf.blit(no_units, (8, UNIT_Y0 + 10))
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
            lbl = F.get('tiny').render('kWh', True, C.TEXT_DIM)
            surf.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.y + 32))

    # Blocked areas indicator
    if p.blocked_areas:
        blocked_txt = 'BLOCKED: ' + ', '.join(
            C.AREA_LABEL.get(a, a) for a in p.blocked_areas if a in C.AREA_LABEL
        )
        b_surf = F.get('tiny').render(blocked_txt, True, C.TEXT_RED)
        surf.blit(b_surf, (8, L.TOPBAR_H + L.MAIN_H - 18))
