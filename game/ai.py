"""Heuristic AI strategies shared by the simulator and PC opponents."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

from game.card import AREAS, Card
from game.engine import TurnEngine
from game.state import GameState, Phase

ENGINEERING = "engineering"


@dataclass(frozen=True)
class Strategy:
    name: str
    description: str
    build_threshold: Callable[[GameState], float]
    research_bias: float = 1.0
    engineering_bias: float = 0.0
    aggression: float = 0.0
    prefer_research: bool = True


def early_build_threshold(state: GameState) -> float:
    return 1.0 if state.round_number <= 4 else 1.4


def balanced_threshold(state: GameState) -> float:
    if state.round_number <= 4:
        return 1.8
    if state.round_number <= 9:
        return 2.8
    return 1.0


def tech_threshold(state: GameState) -> float:
    if state.round_number <= 7:
        return 4.0
    if state.round_number <= 12:
        return 5.5
    return 1.0


def engineering_threshold(state: GameState) -> float:
    return 2.0 if state.round_number <= 8 else 1.0


def aggressive_threshold(state: GameState) -> float:
    return 1.7 if state.round_number <= 8 else 1.0


STRATEGIES: dict[str, Strategy] = {
    "rush": Strategy(
        name="rush",
        description="Builds early and often, mostly drawing weak prototype slots instead of spending full turns on research.",
        build_threshold=early_build_threshold,
        research_bias=0.2,
        prefer_research=False,
    ),
    "balanced": Strategy(
        name="balanced",
        description="Researches for solid prototype upgrades, then starts building once output is respectable.",
        build_threshold=balanced_threshold,
        research_bias=1.0,
    ),
    "tech": Strategy(
        name="tech",
        description="Delays building to chase stronger prototype tiers, aiming for fewer but higher-output units.",
        build_threshold=tech_threshold,
        research_bias=1.6,
    ),
    "engineering": Strategy(
        name="engineering",
        description="Biases toward Engineering cards and farm multipliers while keeping a moderate build threshold.",
        build_threshold=engineering_threshold,
        research_bias=0.7,
        engineering_bias=1.8,
    ),
    "aggressive": Strategy(
        name="aggressive",
        description="Looks for Engineering events, attacks the current leader, and builds on a lower threshold.",
        build_threshold=aggressive_threshold,
        research_bias=0.5,
        engineering_bias=1.1,
        aggression=2.0,
    ),
}


def card_value(card: Card, state: GameState, strategy: Strategy) -> float:
    player = state.current_player
    effect_type = card.effect["type"]

    if effect_type in ("set_junction", "set_optical", "set_contact"):
        slot_name = {
            "set_junction": "junction",
            "set_optical": "optical",
            "set_contact": "contact",
        }[effect_type]
        current_tier = getattr(player.prototype, f"{slot_name}_tier")()
        tier_gain = card.effect["to_tier"] - current_tier
        return (tier_gain * 10.0 + card.effect["to_tier"]) * strategy.research_bias

    if effect_type == "farm_multiplier":
        built_output = sum(player.units)
        return (20.0 * card.effect["delta"] * max(1.0, built_output)) + strategy.engineering_bias

    if effect_type == "event_policy_subsidy":
        return 5.0 + strategy.engineering_bias

    if card.needs_player_target():
        leader_output = max(p.total_output() for p in state.players if p is not player)
        return strategy.aggression * (3.0 + leader_output / 4.0)

    return 0.0


def best_research_area(state: GameState, strategy: Strategy) -> str | None:
    player = state.current_player
    candidates: list[tuple[float, str]] = []

    for area in AREAS:
        if area in player.blocked_areas or len(state.decks[area]) == 0:
            continue
        preview = state.decks[area].peek_top(3)
        if not preview:
            continue
        score = max(card_value(card, state, strategy) for card in preview)
        if area == ENGINEERING:
            score += strategy.engineering_bias
        candidates.append((score, area))

    if not candidates:
        return None
    return max(candidates)[1]


def weakest_slot_area(state: GameState) -> str:
    prototype = state.current_player.prototype
    tiers = {
        "material_science": prototype.junction_tier(),
        "chemistry": prototype.optical_tier(),
        "physics": prototype.contact_tier(),
    }
    return min(tiers, key=tiers.get)


def target_player(state: GameState) -> int:
    opponents = state.opponent_indices()
    return max(opponents, key=lambda idx: state.players[idx].total_output())


def auto_slot_upgrades(engine: TurnEngine) -> None:
    """Play all free hand upgrades that improve a prototype slot."""
    state = engine.state
    improved = True
    while improved and state.phase == Phase.ACTION:
        improved = False
        player = state.current_player
        cards_by_value = sorted(
            list(player.hand),
            key=lambda card: card_value(card, state, STRATEGIES["tech"]),
            reverse=True,
        )
        for card in cards_by_value:
            if not card.is_slot_card():
                continue
            slot_name = {
                "set_junction": "junction",
                "set_optical": "optical",
                "set_contact": "contact",
            }[card.effect["type"]]
            current_tier = getattr(player.prototype, f"{slot_name}_tier")()
            if card.effect["to_tier"] > current_tier:
                engine.select_card(card)
                improved = True
                break


def play_best_immediate(engine: TurnEngine, strategy: Strategy) -> bool:
    state = engine.state
    if state.actions_remaining <= 0:
        return False
    player = state.current_player
    cards = [
        card
        for card in player.hand
        if card.effect["type"] in ("farm_multiplier", "event_policy_subsidy")
    ]
    if not cards:
        return False

    best = max(cards, key=lambda card: card_value(card, state, strategy))
    if card_value(best, state, strategy) < 3.0:
        return False
    before = state.actions_remaining
    engine.select_card(best)
    return state.actions_remaining < before


def play_best_event(engine: TurnEngine, strategy: Strategy) -> bool:
    state = engine.state
    if state.actions_remaining <= 0 or strategy.aggression <= 0:
        return False
    player = state.current_player
    events = [card for card in player.hand if card.needs_player_target()]
    if not events:
        return False

    best = max(events, key=lambda card: card_value(card, state, strategy))
    if card_value(best, state, strategy) < 4.0:
        return False
    engine.select_card(best)
    if state.phase != Phase.TARGETING_PLAYER:
        return False
    return engine.perform_play_event(target_player(state))


def draw_area(state: GameState, strategy: Strategy) -> str | None:
    player = state.current_player
    choices = [area for area in AREAS if area not in player.blocked_areas and len(state.decks[area]) > 0]
    if not choices:
        return None

    if strategy.engineering_bias > 1.0 and ENGINEERING in choices:
        return ENGINEERING

    weak = weakest_slot_area(state)
    if weak in choices:
        return weak

    return random.choice(choices)


def take_research(engine: TurnEngine, strategy: Strategy) -> bool:
    state = engine.state
    if state.actions_remaining < 2:
        return False
    area = best_research_area(state, strategy) if strategy.prefer_research else None
    if area is None:
        return False
    if not engine.enter_research_mode():
        return False
    if not engine.start_research(area):
        engine.deselect_card()
        return False
    choice = max(
        range(len(state.research_choices)),
        key=lambda idx: card_value(state.research_choices[idx], state, strategy),
    )
    return engine.complete_research(choice)


def take_turn_action(engine: TurnEngine, strategy: Strategy) -> None:
    state = engine.state
    player = state.current_player
    auto_slot_upgrades(engine)

    if play_best_event(engine, strategy):
        return
    if play_best_immediate(engine, strategy):
        return

    can_build = player.prototype.kwh_output() >= strategy.build_threshold(state)
    if can_build and engine.perform_build():
        return

    if take_research(engine, strategy):
        return

    area = draw_area(state, strategy)
    if area and engine.perform_draw(area):
        auto_slot_upgrades(engine)
        return

    if engine.perform_build():
        return
    engine.perform_pass()
