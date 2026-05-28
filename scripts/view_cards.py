"""Browse every Solar Rush card and its tooltip text.

Run with:
    uv run scripts/view_cards.py

Controls:
    Mouse wheel / Up / Down / PageUp / PageDown: scroll
    1-4: filter by research area
    0 or A: show all cards
    Esc or Q: quit
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.card import AREAS, Card
import ui.assets as A
import ui.colors as C
import ui.fonts as F
import ui.layout as L
from ui.hand_view import _blit_wrapped, _card_badge
from ui.tooltip import draw_tooltip


WINDOW_W = L.SW
WINDOW_H = L.SH
TOP_H = 78
MARGIN = 18
CARD_W = 220
CARD_H = 310
GAP_X = 20
GAP_Y = 22
AREA_KEYS = {
    pygame.K_1: "material_science",
    pygame.K_2: "chemistry",
    pygame.K_3: "physics",
    pygame.K_4: "engineering",
}


@dataclass(frozen=True)
class CardListing:
    card: Card
    count: int


def card_type_key(card: Card) -> tuple[str, int, str, str, str, str]:
    effect_key = json.dumps(card.effect, sort_keys=True)
    return (
        card.area,
        card.tier,
        card.name,
        card.description,
        card.long_description,
        effect_key,
    )


def load_cards() -> list[Card]:
    path = ROOT / "data" / "cards.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    cards = [Card(**entry) for entry in raw]
    return sorted(cards, key=lambda c: (AREAS.index(c.area), c.tier, c.id))


def unique_card_listings(cards: list[Card]) -> list[CardListing]:
    cards_by_key: dict[tuple[str, int, str, str, str, str], Card] = {}
    counts_by_key: dict[tuple[str, int, str, str, str, str], int] = {}
    for card in cards:
        key = card_type_key(card)
        cards_by_key.setdefault(key, card)
        counts_by_key[key] = counts_by_key.get(key, 0) + 1

    return [
        CardListing(card=card, count=counts_by_key[key])
        for key, card in sorted(
            cards_by_key.items(),
            key=lambda item: (AREAS.index(item[1].area), item[1].tier, item[1].id),
        )
    ]


def filtered_cards(cards: list[CardListing], area_filter: str | None) -> list[CardListing]:
    if area_filter is None:
        return cards
    return [listing for listing in cards if listing.card.area == area_filter]


def max_scroll_for(count: int) -> int:
    cols = max(1, (WINDOW_W - 2 * MARGIN + GAP_X) // (CARD_W + GAP_X))
    rows = (count + cols - 1) // cols
    content_h = rows * CARD_H + max(0, rows - 1) * GAP_Y
    visible_h = WINDOW_H - TOP_H - MARGIN
    return max(0, content_h - visible_h)


def draw_header(
    surf: pygame.Surface,
    area_filter: str | None,
    visible_types: int,
    visible_cards: int,
    total_types: int,
    total_cards: int,
) -> None:
    pygame.draw.rect(surf, C.TOPBAR_BG, pygame.Rect(0, 0, WINDOW_W, TOP_H))
    title = F.get("large").render("Solar Rush Card Browser", True, C.WHITE)
    surf.blit(title, (MARGIN, 10))

    count = F.get("small").render(
        f"{visible_types} / {total_types} types  |  {visible_cards} / {total_cards} cards",
        True,
        C.TEXT_DIM,
    )
    surf.blit(count, (title.get_rect(x=MARGIN, y=10).right + 18, 20))

    x = WINDOW_W - 746
    all_selected = area_filter is None
    x = draw_filter_label(surf, x, "0", "All", C.CYAN, all_selected)
    for idx, area in enumerate(AREAS, start=1):
        label = C.AREA_LABEL.get(area, area)
        x = draw_filter_label(surf, x, str(idx), label, C.AREA[area], area_filter == area)


def draw_filter_label(
    surf: pygame.Surface,
    x: int,
    key: str,
    label: str,
    color: tuple[int, int, int],
    selected: bool,
) -> int:
    font = F.get("tiny")
    text = f"{key} {label}"
    text_surf = font.render(text, True, C.WHITE if selected else color)
    rect = pygame.Rect(x, 16, text_surf.get_width() + 16, 26)
    if selected:
        pygame.draw.rect(surf, color, rect, border_radius=5)
    else:
        pygame.draw.rect(surf, color, rect, 1, border_radius=5)
    surf.blit(text_surf, (rect.x + 8, rect.y + 4))
    return rect.right + 8


def draw_cards(
    surf: pygame.Surface,
    cards: list[CardListing],
    scroll_y: int,
    mouse_pos: tuple[int, int],
) -> Card | None:
    cols = max(1, (WINDOW_W - 2 * MARGIN + GAP_X) // (CARD_W + GAP_X))
    hovered_card = None

    for idx, listing in enumerate(cards):
        row, col = divmod(idx, cols)
        card = listing.card
        x = MARGIN + col * (CARD_W + GAP_X)
        y = TOP_H + MARGIN + row * (CARD_H + GAP_Y) - scroll_y
        rect = pygame.Rect(x, y, CARD_W, CARD_H)

        if rect.bottom < TOP_H or rect.top > WINDOW_H:
            continue

        hovered = rect.collidepoint(mouse_pos)
        draw_browser_card(surf, card, listing.count, rect, hovered)
        if hovered:
            hovered_card = card

    return hovered_card


def draw_browser_card(
    surf: pygame.Surface,
    card: Card,
    count: int,
    rect: pygame.Rect,
    hovered: bool,
) -> None:
    area_color = C.AREA.get(card.area, C.CELL_BORDER)
    area_dark = C.AREA_DARK.get(card.area, C.CELL_BG)

    bg = C.BTN_HOVER if hovered else C.CELL_BG
    border = area_color if hovered else C.CELL_BORDER
    border_w = 2 if hovered else 1

    pygame.draw.rect(surf, bg, rect, border_radius=7)
    pygame.draw.rect(surf, border, rect, border_w, border_radius=7)

    band = pygame.Rect(rect.x + border_w, rect.y + border_w, rect.width - 2 * border_w, 33)
    pygame.draw.rect(surf, area_dark, band)
    area_lbl = F.get("tiny").render(C.AREA_LABEL.get(card.area, card.area), True, area_color)
    surf.blit(area_lbl, (band.x + 6, band.y + 4))

    badge_txt = _card_badge(card)
    badge_top = F.get("bold").render(badge_txt, True, C.WHITE)
    surf.blit(badge_top, (band.right - badge_top.get_width() - 6, band.y + 2))

    if count > 1:
        count_txt = F.get("tiny").render(f"x{count}", True, C.WHITE)
        count_rect = pygame.Rect(
            rect.right - count_txt.get_width() - 16,
            rect.y + 39,
            count_txt.get_width() + 10,
            21,
        )
        pygame.draw.rect(surf, area_color, count_rect, border_radius=5)
        surf.blit(count_txt, (count_rect.x + 5, count_rect.y + 3))

    _blit_wrapped(surf, card.name, F.get("bold"), C.TEXT_MAIN, rect.x + 8, rect.y + 46, rect.width - 16, 2)

    art_rect = pygame.Rect(rect.x + 12, rect.y + 116, rect.width - 24, 92)
    art = A.get_card_image(card.id, art_rect.width, art_rect.height)
    surf.blit(art, art_rect)
    pygame.draw.rect(surf, area_color, art_rect, 1, border_radius=4)

    _blit_wrapped(surf, card.description, F.get("tiny"), C.TEXT_DIM, rect.x + 8, rect.y + 220, rect.width - 16, 2)

    badge = F.get("bold").render(badge_txt, True, C.WHITE)
    surf.blit(badge, (rect.centerx - badge.get_width() // 2, rect.bottom - 31))


def draw(
    surf: pygame.Surface,
    all_cards: list[CardListing],
    total_cards: int,
    area_filter: str | None,
    scroll_y: int,
    mouse_pos: tuple[int, int],
) -> None:
    cards = filtered_cards(all_cards, area_filter)
    visible_cards = sum(listing.count for listing in cards)
    surf.fill(C.BG)
    hovered_card = draw_cards(surf, cards, scroll_y, mouse_pos)
    draw_header(surf, area_filter, len(cards), visible_cards, len(all_cards), total_cards)
    if hovered_card is not None:
        draw_tooltip(surf, hovered_card, mouse_pos)


def clamp_scroll(scroll_y: int, card_count: int) -> int:
    return max(0, min(scroll_y, max_scroll_for(card_count)))


def scale_mouse(pos: tuple[int, int], screen_size: tuple[int, int]) -> tuple[int, int]:
    screen_w, screen_h = screen_size
    if screen_w <= 0 or screen_h <= 0:
        return pos
    return (int(pos[0] * WINDOW_W / screen_w), int(pos[1] * WINDOW_H / screen_h))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--area",
        choices=AREAS,
        help="Start with one research area selected.",
    )
    parser.add_argument(
        "--screenshot",
        type=Path,
        help="Render one frame to this PNG and exit.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pygame.init()
    F.load()
    A.load()

    cards = load_cards()
    card_listings = unique_card_listings(cards)
    area_filter = args.area
    scroll_y = 0

    if args.screenshot:
        surf = pygame.Surface((WINDOW_W, WINDOW_H))
        draw(
            surf,
            card_listings,
            len(cards),
            area_filter,
            scroll_y,
            (MARGIN + 12, TOP_H + MARGIN + 12),
        )
        pygame.image.save(surf, args.screenshot)
        return

    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.RESIZABLE)
    pygame.display.set_caption("Solar Rush Card Browser")
    clock = pygame.time.Clock()

    running = True
    while running:
        visible_cards = filtered_cards(card_listings, area_filter)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEWHEEL:
                scroll_y = clamp_scroll(scroll_y - event.y * 58, len(visible_cards))
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key in (pygame.K_0, pygame.K_a):
                    area_filter = None
                    scroll_y = clamp_scroll(scroll_y, len(filtered_cards(card_listings, area_filter)))
                elif event.key in AREA_KEYS:
                    area_filter = AREA_KEYS[event.key]
                    scroll_y = clamp_scroll(scroll_y, len(filtered_cards(card_listings, area_filter)))
                elif event.key == pygame.K_DOWN:
                    scroll_y = clamp_scroll(scroll_y + 58, len(visible_cards))
                elif event.key == pygame.K_UP:
                    scroll_y = clamp_scroll(scroll_y - 58, len(visible_cards))
                elif event.key == pygame.K_PAGEDOWN:
                    scroll_y = clamp_scroll(scroll_y + 520, len(visible_cards))
                elif event.key == pygame.K_PAGEUP:
                    scroll_y = clamp_scroll(scroll_y - 520, len(visible_cards))

        mouse_pos = scale_mouse(pygame.mouse.get_pos(), screen.get_size())
        logical = pygame.Surface((WINDOW_W, WINDOW_H))
        draw(logical, card_listings, len(cards), area_filter, scroll_y, mouse_pos)
        pygame.transform.smoothscale(logical, screen.get_size(), screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
