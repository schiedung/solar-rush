import pygame

from game.card import Card
import ui.colors as C
import ui.layout as L

_PADDING = 10
_LINE_HEIGHT_BODY = 16
_LINE_HEIGHT_TITLE = 20
_MAX_TOOLTIP_W = 360


def draw_tooltip(
    surf: pygame.Surface,
    card: Card,
    mouse_pos: tuple[int, int],
) -> None:
    if not card.long_description:
        return

    import ui.fonts as F

    title_font = F.get('bold')
    body_font = F.get('small')
    badge_font = F.get('tiny')

    area_color = C.AREA.get(card.area, C.CELL_BORDER)
    area_label = C.AREA_LABEL.get(card.area, card.area)

    from ui.hand_view import _card_badge
    badge = _card_badge(card)

    title_line = f'{card.name}'
    header_line = f'{area_label}  ·  {badge}' if badge else area_label

    max_w = _MAX_TOOLTIP_W - 2 * _PADDING
    desc_lines = _wrap_text(card.long_description, body_font, max_w)

    title_surf = title_font.render(title_line, True, C.TEXT_MAIN)
    header_surf = badge_font.render(header_line, True, area_color)
    desc_surfs = [body_font.render(ln, True, C.TEXT_DIM) for ln in desc_lines]

    content_w = max(
        title_surf.get_width(),
        header_surf.get_width(),
        max((s.get_width() for s in desc_surfs), default=0),
    )
    content_w = min(content_w, max_w)

    content_h = (
        title_surf.get_height() + 4
        + header_surf.get_height() + 6
        + len(desc_surfs) * _LINE_HEIGHT_BODY
    )

    box_w = content_w + 2 * _PADDING
    box_h = content_h + 2 * _PADDING

    tx, ty = mouse_pos[0] + 18, mouse_pos[1] + 18

    if tx + box_w > L.SW - 4:
        tx = mouse_pos[0] - box_w - 12
    if ty + box_h > L.SH - 4:
        ty = mouse_pos[1] - box_h - 12
    if tx < 4:
        tx = 4
    if ty < 4:
        ty = 4

    box_rect = pygame.Rect(tx, ty, box_w, box_h)

    bg_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    bg_surf.fill((*C.BASE02, 240))
    surf.blit(bg_surf, box_rect.topleft)

    pygame.draw.rect(surf, area_color, box_rect, 2, border_radius=8)

    y = ty + _PADDING
    surf.blit(title_surf, (tx + _PADDING, y))
    y += title_surf.get_height() + 4
    surf.blit(header_surf, (tx + _PADDING, y))
    y += header_surf.get_height() + 6
    for ds in desc_surfs:
        surf.blit(ds, (tx + _PADDING, y))
        y += _LINE_HEIGHT_BODY


def _wrap_text(text: str, font: pygame.font.Font, max_w: int) -> list[str]:
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
    if line:
        lines.append(line)
    return lines
