from dataclasses import dataclass, field
import pygame

from game.card import Card
from game.state import GameState, Phase
import ui.colors as C
import ui.fonts as F
import ui.layout as L
import ui.assets as A
import ui.progress_track as track_view
import ui.farm_view as farm_view
import ui.hand_view as hand_view
import ui.deck_panel as deck_panel
import ui.event_overlay as overlay
import ui.tooltip as tooltip


@dataclass
class UIRects:
    hand_rects: list[pygame.Rect] = field(default_factory=list)
    token_rects: list[pygame.Rect] = field(default_factory=list)
    research_rects: list[pygame.Rect] = field(default_factory=list)
    player_target_rects: list[pygame.Rect] = field(default_factory=list)
    slot_rects: dict[str, pygame.Rect] = field(default_factory=dict)
    handoff_btn: pygame.Rect = field(default_factory=lambda: pygame.Rect(0, 0, 0, 0))
    play_again_btn: pygame.Rect = field(default_factory=lambda: pygame.Rect(0, 0, 0, 0))
    hovered_card: Card | None = None


def draw(surf: pygame.Surface, state: GameState, mouse_pos: tuple) -> UIRects:
    surf.blit(A.get('background', L.SW, L.SH), (0, 0))
    rects = UIRects()
    input_mouse = (-1, -1) if state.current_player.is_ai else mouse_pos

    rects.token_rects = track_view.draw(surf, state)
    slot_result = farm_view.draw(surf, state, input_mouse)
    rects.slot_rects = slot_result['unslot_rects']
    rects.hovered_card = slot_result.get('hovered_card')
    deck_panel.draw(surf, state, input_mouse)
    hand_result = hand_view.draw(surf, state, input_mouse)
    rects.hand_rects = hand_result['rects']
    if hand_result.get('hovered_card'):
        rects.hovered_card = hand_result['hovered_card']

    if state.current_player.is_ai:
        rects.slot_rects = {}
        rects.hand_rects = []

    phase = state.phase
    if phase == Phase.HANDOFF and not state.current_player.is_ai:
        rects.handoff_btn = L.FINISH_TURN_BTN
    elif phase == Phase.GAME_OVER:
        rects.play_again_btn = overlay.draw_game_over(surf, state, mouse_pos)
    elif phase == Phase.RESEARCH_CHOOSE:
        rects.research_rects = overlay.draw_research_choose(surf, state, mouse_pos)
        for i, research_rect in enumerate(rects.research_rects):
            if research_rect.collidepoint(mouse_pos) and i < len(state.research_choices):
                rects.hovered_card = state.research_choices[i]
                break
    elif phase == Phase.TARGETING_PLAYER:
        rects.player_target_rects = overlay.draw_player_target(surf, state, mouse_pos)

    if (
        not state.current_player.is_ai
        and rects.hovered_card
        and phase in (Phase.ACTION, Phase.HANDOFF, Phase.RESEARCH_CHOOSE, Phase.TARGETING_PLAYER)
    ):
        tooltip.draw_tooltip(surf, rects.hovered_card, mouse_pos)

    if state.current_player.is_ai and phase != Phase.GAME_OVER:
        overlay.draw_pc_turn_banner(surf, state)

    return rects
