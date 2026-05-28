from dataclasses import dataclass, field
import pygame

from game.state import GameState, Phase
import ui.colors as C
import ui.fonts as F
import ui.layout as L
import ui.progress_track as track_view
import ui.farm_view as farm_view
import ui.hand_view as hand_view
import ui.deck_panel as deck_panel
import ui.event_overlay as overlay


@dataclass
class UIRects:
    hand_rects: list[pygame.Rect] = field(default_factory=list)
    token_rects: list[pygame.Rect] = field(default_factory=list)
    research_rects: list[pygame.Rect] = field(default_factory=list)
    player_target_rects: list[pygame.Rect] = field(default_factory=list)
    slot_rects: dict[str, pygame.Rect] = field(default_factory=dict)
    handoff_btn: pygame.Rect = field(default_factory=lambda: pygame.Rect(0, 0, 0, 0))
    play_again_btn: pygame.Rect = field(default_factory=lambda: pygame.Rect(0, 0, 0, 0))


def draw(surf: pygame.Surface, state: GameState, mouse_pos: tuple) -> UIRects:
    surf.fill(C.BG)
    rects = UIRects()

    rects.token_rects = track_view.draw(surf, state)
    rects.slot_rects = farm_view.draw(surf, state, mouse_pos)
    deck_panel.draw(surf, state, mouse_pos)
    rects.hand_rects = hand_view.draw(surf, state, mouse_pos)

    phase = state.phase
    if phase == Phase.HANDOFF:
        rects.handoff_btn = L.FINISH_TURN_BTN
    elif phase == Phase.GAME_OVER:
        rects.play_again_btn = overlay.draw_game_over(surf, state, mouse_pos)
    elif phase == Phase.RESEARCH_CHOOSE:
        rects.research_rects = overlay.draw_research_choose(surf, state, mouse_pos)
    elif phase == Phase.TARGETING_PLAYER:
        rects.player_target_rects = overlay.draw_player_target(surf, state, mouse_pos)

    return rects
