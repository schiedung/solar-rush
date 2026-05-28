import pygame

from game.state import GameState, RACE_TARGET_KW, MAX_ROUNDS
import ui.colors as C
import ui.fonts as F
import ui.layout as L
import ui.assets as A


def draw(surf: pygame.Surface, state: GameState) -> list[pygame.Rect]:
    """Draw the progress track. Returns player token rects for click detection."""
    rail = A.get('track_rail', L.TRACK_USABLE, 51)
    surf.blit(rail, (L.TRACK_X0, L.TRACK_Y - 26))

    # Goal star
    x_goal = L.kwh_to_x(RACE_TARGET_KW, RACE_TARGET_KW)
    goal_star = A.get('goal_star', 63, 63)
    surf.blit(goal_star, (x_goal - 32, L.TRACK_Y - 65))

    # Player tokens — draw in reverse so P1 is on top when overlapping
    token_rects: list[pygame.Rect] = []
    for i in range(len(state.players) - 1, -1, -1):
        player = state.players[i]
        x = L.kwh_to_x(player.total_output(), RACE_TARGET_KW)
        y = L.TRACK_Y
        pygame.draw.circle(surf, C.BLACK, (x + 2, y + 2), L.TOKEN_R)
        pygame.draw.circle(surf, player.color, (x, y), L.TOKEN_R)
        ring = A.get('token_ring', 57, 57)
        surf.blit(ring, (x - 29, y - 29))
        if i == state.current_player_idx:
            pygame.draw.circle(surf, C.WHITE, (x, y), L.TOKEN_R + 3, 2)
        num = F.get('bold').render(str(i + 1), True, C.WHITE)
        surf.blit(num, (x - num.get_width() // 2, y - num.get_height() // 2))
        tr = pygame.Rect(x - L.TOKEN_R, y - L.TOKEN_R, L.TOKEN_R * 2, L.TOKEN_R * 2)
        token_rects.append(tr)

    token_rects.reverse()

    # Info strip
    p = state.current_player
    info = (
        f'Round {state.round_number}/{MAX_ROUNDS}   |   '
        f'{p.name}\'s Turn   |   '
        f'Actions: {state.actions_remaining}'
    )
    info_surf = F.get('medium').render(info, True, C.TEXT_MAIN)
    surf.blit(info_surf, (L.SW // 2 - info_surf.get_width() // 2, 117))

    if state.last_event_message:
        msg_surf = F.get('small').render(state.last_event_message, True, C.TEXT_GOLD)
        surf.blit(msg_surf, (L.SW // 2 - msg_surf.get_width() // 2, 146))

    return token_rects
