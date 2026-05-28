import pygame

from game.cell import SolarCell, MAX_TIER
from game.state import GameState, Phase
import ui.colors as C
import ui.fonts as F
import ui.layout as L


_PART_LABELS = ('J', 'O', 'C')   # Junction, Optical, Contact
_PART_AREAS  = ('material_science', 'chemistry', 'physics')


def _draw_cell(
    surf: pygame.Surface,
    cell: SolarCell,
    rect: pygame.Rect,
    targetable: bool,
    selected: bool,
) -> None:
    border_color = C.CELL_SELECT if selected else (C.CELL_TARGET if targetable else C.CELL_BORDER)
    border_w = 3 if (targetable or selected) else 1

    pygame.draw.rect(surf, C.CELL_BG, rect, border_radius=6)
    pygame.draw.rect(surf, border_color, rect, border_w, border_radius=6)

    # kWh output
    kwh = cell.kwh_output()
    kwh_surf = F.get('bold').render(f'{kwh:.2f} kWh', True, C.TEXT_GOLD)
    surf.blit(kwh_surf, (rect.centerx - kwh_surf.get_width() // 2, rect.y + 6))

    # Three tier bars (Junction, Optical, Contact)
    tiers = (cell.junction_tier, cell.optical_tier, cell.contact_tier)
    bar_w = (rect.width - 14) // 3
    bar_h = 38
    bar_y = rect.y + 30
    gap = 4

    for k, (tier, label, area) in enumerate(zip(tiers, _PART_LABELS, _PART_AREAS)):
        bx = rect.x + 7 + k * (bar_w + gap)
        # Background slot
        pygame.draw.rect(surf, C.AREA_DARK[area], (bx, bar_y, bar_w, bar_h), border_radius=3)
        # Filled portion
        fill_h = int(bar_h * (tier / MAX_TIER)) if tier > 0 else 2
        fill_color = C.TIER_COLORS[tier]
        pygame.draw.rect(surf, fill_color,
                         (bx, bar_y + bar_h - fill_h, bar_w, fill_h),
                         border_radius=3)
        # Label
        lbl = F.get('tiny').render(label, True, C.TEXT_DIM)
        surf.blit(lbl, (bx + bar_w // 2 - lbl.get_width() // 2, bar_y + bar_h + 3))

    # Part names (tiny, multi-line)
    names = cell.part_names()
    part_name_texts = [
        names['junction'][:8],
        names['optical'][:8],
        names['contact'][:8],
    ]
    y_off = bar_y + bar_h + 18
    for k, txt in enumerate(part_name_texts):
        bx = rect.x + 7 + k * (bar_w + gap)
        lbl = F.get('tiny').render(txt, True, C.TEXT_DIM)
        surf.blit(lbl, (bx + bar_w // 2 - lbl.get_width() // 2, y_off))


def draw(
    surf: pygame.Surface,
    state: GameState,
    mouse_pos: tuple[int, int],
) -> list[pygame.Rect]:
    """Draw the current player's farm. Returns list of cell rects."""
    # Farm background
    pygame.draw.rect(surf, C.FARM_BG, (0, L.TOPBAR_H, L.FARM_W, L.MAIN_H))
    pygame.draw.line(surf, C.DIVIDER, (L.FARM_W, L.TOPBAR_H), (L.FARM_W, L.TOPBAR_H + L.MAIN_H), 2)

    # Farm label
    p = state.current_player
    lbl = F.get('body').render(
        f"{p.name}'s Farm  —  {p.total_output():.1f} kWh/turn"
        f"  (×{1.0 + p.farm_bonus:.2f} bonus)",
        True, C.TEXT_DIM
    )
    surf.blit(lbl, (12, L.TOPBAR_H + 2))

    # Blocked areas indicator
    if p.blocked_areas:
        blocked_txt = 'Blocked: ' + ', '.join(
            C.AREA_LABEL[a] for a in p.blocked_areas if a in C.AREA_LABEL
        )
        b_surf = F.get('tiny').render(blocked_txt, True, C.TEXT_RED)
        surf.blit(b_surf, (12, L.TOPBAR_H + 18))

    # Cells
    is_targeting = state.phase == Phase.TARGETING_CELL
    cell_rects: list[pygame.Rect] = []

    for i, cell in enumerate(p.farm):
        rect = L.cell_rect(i)
        if rect.bottom > L.TOPBAR_H + L.MAIN_H - 4:
            break  # don't overflow into hand area
        hovered = rect.collidepoint(mouse_pos)
        targetable = is_targeting and not hovered
        selected_hover = is_targeting and hovered
        _draw_cell(surf, cell, rect, targetable, selected_hover)
        cell_rects.append(rect)

    return cell_rects
