import math
import pygame

from game.state import GameState, RACE_TARGET_KW
import ui.colors as C
import ui.fonts as F
import ui.layout as L


_MILESTONES = [0, 5, 10, 15, int(RACE_TARGET_KW)]


def _star(cx: int, cy: int, outer: int, inner: int) -> list:
    pts = []
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        r = outer if i % 2 == 0 else inner
        pts.append((cx + r * math.cos(angle), cy - r * math.sin(angle)))
    return pts


def draw(surf: pygame.Surface, state: GameState) -> list[pygame.Rect]:
    """Draw the progress track. Returns player token rects for click detection."""
    pygame.draw.rect(surf, C.TOPBAR_BG, (0, 0, L.SW, L.TOPBAR_H))
    pygame.draw.rect(surf, C.TRACK_BG, (18, 5, L.SW - 36, 68), border_radius=8)

    # Rail line
    pygame.draw.line(surf, (42, 120, 140), (L.TRACK_X0, L.TRACK_Y), (L.TRACK_X1, L.TRACK_Y), 3)

    # Milestone markers
    for kw in _MILESTONES:
        x = L.kwh_to_x(kw, RACE_TARGET_KW)
        is_target = (kw == RACE_TARGET_KW)
        color = C.TEXT_GOLD if is_target else C.TEXT_DIM
        tick_h = 12 if is_target else 7
        pygame.draw.line(surf, color, (x, L.TRACK_Y - tick_h), (x, L.TRACK_Y + tick_h), 2)
        lbl = F.get('tiny').render(f'{int(kw)} kW', True, color)
        surf.blit(lbl, (x - lbl.get_width() // 2, L.TRACK_Y + 16))

    # Goal star
    x_goal = L.kwh_to_x(RACE_TARGET_KW, RACE_TARGET_KW)
    pygame.draw.polygon(surf, C.TEXT_GOLD, _star(x_goal, L.TRACK_Y - 22, 10, 4))

    # Player tokens — draw in reverse so P1 is on top when overlapping
    token_rects: list[pygame.Rect] = []
    for i in range(len(state.players) - 1, -1, -1):
        player = state.players[i]
        x = L.kwh_to_x(player.total_output(), RACE_TARGET_KW)
        y = L.TRACK_Y
        pygame.draw.circle(surf, C.BLACK, (x + 2, y + 2), L.TOKEN_R)
        pygame.draw.circle(surf, player.color, (x, y), L.TOKEN_R)
        border = C.WHITE if i == state.current_player_idx else (100, 100, 130)
        pygame.draw.circle(surf, border, (x, y), L.TOKEN_R, 2)
        num = F.get('bold').render(str(i + 1), True, C.WHITE)
        surf.blit(num, (x - num.get_width() // 2, y - num.get_height() // 2))
        tr = pygame.Rect(x - L.TOKEN_R, y - L.TOKEN_R, L.TOKEN_R * 2, L.TOKEN_R * 2)
        token_rects.append(tr)

    token_rects.reverse()

    # Info strip
    p = state.current_player
    info = (
        f'Round {state.round_number}/20   |   '
        f'{p.name}\'s Turn   |   '
        f'Actions: {state.actions_remaining}'
    )
    info_surf = F.get('medium').render(info, True, C.TEXT_MAIN)
    surf.blit(info_surf, (L.SW // 2 - info_surf.get_width() // 2, 78))

    if state.last_event_message:
        msg_surf = F.get('small').render(state.last_event_message, True, C.TEXT_GOLD)
        surf.blit(msg_surf, (L.SW // 2 - msg_surf.get_width() // 2, 97))

    return token_rects
