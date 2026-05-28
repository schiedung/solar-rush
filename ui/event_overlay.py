import pygame

from game.card import Card
from game.state import GameState, Phase
import ui.colors as C
import ui.fonts as F
import ui.layout as L
import ui.assets as A
from ui.hand_view import _card_badge


def _dim_screen(surf: pygame.Surface) -> None:
    overlay = pygame.Surface((L.SW, L.SH), pygame.SRCALPHA)
    overlay.fill(C.OVERLAY_DIM)
    surf.blit(overlay, (0, 0))


def _panel(surf: pygame.Surface, w: int, h: int) -> pygame.Rect:
    rect = pygame.Rect((L.SW - w) // 2, (L.SH - h) // 2, w, h)
    pygame.draw.rect(surf, C.BASE02, rect, border_radius=12)
    pygame.draw.rect(surf, C.BLUE, rect, 2, border_radius=12)
    return rect


def draw_pc_turn_banner(surf: pygame.Surface, state: GameState) -> None:
    rect = pygame.Rect((L.SW - 460) // 2, 82, 460, 48)
    banner = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(banner, (*C.BASE02, 210), banner.get_rect(), border_radius=8)
    pygame.draw.rect(banner, (*C.TEXT_GOLD, 230), banner.get_rect(), 2, border_radius=8)
    surf.blit(banner, rect)

    label = F.get('large').render(f'{state.current_player.name} is playing', True, C.TEXT_GOLD)
    surf.blit(label, (rect.centerx - label.get_width() // 2,
                      rect.centery - label.get_height() // 2))



def draw_game_over(surf: pygame.Surface, state: GameState, mouse_pos: tuple) -> pygame.Rect:
    _dim_screen(surf)
    panel = _panel(surf, 560, 380)

    title = F.get('title').render('GAME OVER', True, C.TEXT_GOLD)
    surf.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 24))

    if state.winner:
        win = F.get('large').render(f'{state.winner.name} wins!', True, state.winner.color)
        surf.blit(win, (panel.centerx - win.get_width() // 2, panel.y + 72))

    y = panel.y + 116
    for i, p in enumerate(sorted(state.players, key=lambda x: -x.total_output())):
        highlight = p is state.winner
        col = p.color if highlight else C.TEXT_DIM
        rank = F.get('body').render(f'#{i+1}  {p.name}:  {p.total_output():.2f} kW', True, col)
        surf.blit(rank, (panel.centerx - rank.get_width() // 2, y + i * 30))

    btn = L.PLAY_AGAIN_BTN
    hovered = btn.collidepoint(mouse_pos)
    pygame.draw.rect(surf, C.BTN_HOVER if hovered else C.BTN_NORMAL, btn, border_radius=8)
    pygame.draw.rect(surf, C.TEXT_GOLD, btn, 2, border_radius=8)
    lbl = F.get('large').render('Play Again', True, C.TEXT_GOLD)
    surf.blit(lbl, (btn.centerx - lbl.get_width() // 2, btn.centery - lbl.get_height() // 2))

    return btn


def draw_research_choose(
    surf: pygame.Surface,
    state: GameState,
    mouse_pos: tuple,
) -> list[pygame.Rect]:
    _dim_screen(surf)
    panel = _panel(surf, 700, 340)

    title = F.get('large').render('Research — Choose a card to keep', True, C.TEXT_MAIN)
    surf.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 16))

    rects: list[pygame.Rect] = []
    for i, card in enumerate(state.research_choices):
        rect = L.research_card_rect(i, len(state.research_choices))
        hovered = rect.collidepoint(mouse_pos)
        area_color = C.AREA.get(card.area, C.BTN_BORDER)
        bg = C.BTN_HOVER if hovered else C.CELL_BG
        border = area_color if hovered else C.CELL_BORDER

        pygame.draw.rect(surf, bg, rect, border_radius=8)
        pygame.draw.rect(surf, border, rect, 2, border_radius=8)

        name_surf = F.get('bold').render(card.name, True, C.TEXT_MAIN)
        surf.blit(name_surf, (rect.centerx - name_surf.get_width() // 2, rect.y + 12))

        area_surf = F.get('tiny').render(
            C.AREA_LABEL.get(card.area, card.area), True, area_color
        )
        surf.blit(area_surf, (rect.centerx - area_surf.get_width() // 2, rect.y + 36))

        badge_surf = F.get('bold').render(_card_badge(card), True, C.WHITE)
        surf.blit(badge_surf, (rect.centerx - badge_surf.get_width() // 2, rect.y + 52))

        art_rect = pygame.Rect(rect.x + 10, rect.y + 76, rect.width - 20, 76)
        art = A.get_card_image(card.id, art_rect.width, art_rect.height)
        surf.blit(art, art_rect)
        pygame.draw.rect(surf, area_color, art_rect, 1, border_radius=5)

        y_off = rect.y + 160
        for line in _wrap(card.description, F.get('tiny'), rect.width - 10):
            s = F.get('tiny').render(line, True, C.TEXT_DIM)
            surf.blit(s, (rect.x + 5, y_off))
            y_off += F.get('tiny').get_height() + 2

        rects.append(rect)

    return rects


def draw_player_target(
    surf: pygame.Surface,
    state: GameState,
    mouse_pos: tuple,
) -> list[pygame.Rect]:
    _dim_screen(surf)
    panel = _panel(surf, 440, 80 + len(state.players) * 60)

    title = F.get('large').render('Select Target Player', True, C.TEXT_MAIN)
    surf.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 16))

    btns: list[pygame.Rect] = []
    for i, p in enumerate(state.players):
        if i == state.current_player_idx:
            btns.append(pygame.Rect(0, 0, 0, 0))
            continue
        btn = pygame.Rect(panel.x + 60, panel.y + 58 + i * 60, panel.width - 120, 46)
        hovered = btn.collidepoint(mouse_pos)
        pygame.draw.rect(surf, C.BTN_HOVER if hovered else C.BTN_NORMAL, btn, border_radius=8)
        pygame.draw.rect(surf, p.color, btn, 2, border_radius=8)
        lbl = F.get('bold').render(
            f'{p.name}  —  {p.total_output():.2f} kW', True, p.color
        )
        surf.blit(lbl, (btn.centerx - lbl.get_width() // 2,
                        btn.centery - lbl.get_height() // 2))
        btns.append(btn)

    return btns


def _wrap(text: str, font: pygame.font.Font, max_w: int) -> list[str]:
    words = text.split()
    lines, line = [], ''
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
