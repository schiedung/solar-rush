import math
import pygame

from game.state import GameState, RACE_TARGET_KW
import ui.colors as C
import ui.fonts as F
import ui.layout as L
import ui.assets as A


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
    top_overlay = pygame.Surface((L.SW, L.TOPBAR_H), pygame.SRCALPHA)
    top_overlay.fill((*C.TOPBAR_BG, 150))
    surf.blit(top_overlay, (0, 0))

    track_bg = pygame.Surface((L.SW - 36, 68), pygame.SRCALPHA)
    pygame.draw.rect(track_bg, (*C.TRACK_BG, 185), track_bg.get_rect(), border_radius=8)
    pygame.draw.rect(track_bg, (*C.TEXT_GOLD, 95), track_bg.get_rect(), 1, border_radius=8)
    surf.blit(track_bg, (18, 5))

    # Rail line
    rail = A.get('track_rail', L.TRACK_USABLE, 34)
    surf.blit(rail, (L.TRACK_X0, L.TRACK_Y - 17))

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
    goal_star = A.get('goal_star', 42, 42)
    surf.blit(goal_star, (x_goal - 21, L.TRACK_Y - 43))

    # Player tokens — draw in reverse so P1 is on top when overlapping
    token_rects: list[pygame.Rect] = []
    for i in range(len(state.players) - 1, -1, -1):
        player = state.players[i]
        x = L.kwh_to_x(player.total_output(), RACE_TARGET_KW)
        y = L.TRACK_Y
        pygame.draw.circle(surf, C.BLACK, (x + 2, y + 2), L.TOKEN_R)
        pygame.draw.circle(surf, player.color, (x, y), L.TOKEN_R)
        ring = A.get('token_ring', 38, 38)
        surf.blit(ring, (x - 19, y - 19))
        if i == state.current_player_idx:
            pygame.draw.circle(surf, C.WHITE, (x, y), L.TOKEN_R + 2, 2)
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
