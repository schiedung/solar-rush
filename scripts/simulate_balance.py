"""Monte Carlo balance simulator for Solar Rush.

The simulator intentionally drives the production game engine instead of a
separate rules model. That keeps balance reports aligned with the playable game.
"""

from __future__ import annotations

import argparse
import random
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.card import AREAS, Card
from game.engine import TurnEngine
from game.state import MAX_ROUNDS, RACE_TARGET_KW, GameState, Phase, make_game

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


@dataclass
class PlayerResult:
    strategy: str
    final_output: float
    units: int
    farm_bonus: float
    prototype_output: float


@dataclass
class GameResult:
    winner_idx: int
    winner_strategy: str
    finish_round: int
    ended_by_race: bool
    player_results: list[PlayerResult]
    first_player_won: bool


@dataclass
class StrategyStats:
    games: int = 0
    wins: int = 0
    race_wins: int = 0
    finish_rounds: list[int] = field(default_factory=list)
    outputs: list[float] = field(default_factory=list)
    units: list[int] = field(default_factory=list)
    farm_bonuses: list[float] = field(default_factory=list)
    prototype_outputs: list[float] = field(default_factory=list)

    def record_player(self, result: PlayerResult) -> None:
        self.games += 1
        self.outputs.append(result.final_output)
        self.units.append(result.units)
        self.farm_bonuses.append(result.farm_bonus)
        self.prototype_outputs.append(result.prototype_output)

    def record_win(self, finish_round: int, ended_by_race: bool) -> None:
        self.wins += 1
        self.finish_rounds.append(finish_round)
        if ended_by_race:
            self.race_wins += 1


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


def simulate_game(strategy_names: list[str], seed: int | None = None) -> GameResult:
    if seed is not None:
        random.seed(seed)

    state = make_game(len(strategy_names))
    strategies = [STRATEGIES[name] for name in strategy_names]
    engine = TurnEngine(state)

    guard = 0
    while state.phase != Phase.GAME_OVER:
        guard += 1
        if guard > 10_000:
            raise RuntimeError("simulation did not terminate")

        if state.phase == Phase.ACTION:
            strategy = strategies[state.current_player_idx]
            take_turn_action(engine, strategy)
        elif state.phase == Phase.HANDOFF:
            engine.advance_to_next_player()
        else:
            engine.deselect_card()

    winner_idx = state.players.index(state.winner) if state.winner else 0
    ended_by_race = bool(state.winner and state.winner.total_output() >= RACE_TARGET_KW)
    player_results = [
        PlayerResult(
            strategy=strategies[idx].name,
            final_output=player.total_output(),
            units=len(player.units),
            farm_bonus=player.farm_bonus,
            prototype_output=player.prototype.kwh_output(),
        )
        for idx, player in enumerate(state.players)
    ]
    return GameResult(
        winner_idx=winner_idx,
        winner_strategy=strategies[winner_idx].name,
        finish_round=state.round_number,
        ended_by_race=ended_by_race,
        player_results=player_results,
        first_player_won=winner_idx == 0,
    )


def mean(values: list[float] | list[int]) -> float:
    return statistics.fmean(values) if values else 0.0


def percentile(values: list[int], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, round((len(ordered) - 1) * pct))
    return float(ordered[idx])


def print_report(results: list[GameResult], strategy_names: list[str], fixed_seats: bool) -> None:
    stats: dict[str, StrategyStats] = defaultdict(StrategyStats)
    winner_counts = Counter(result.winner_strategy for result in results)
    race_finishes = sum(result.ended_by_race for result in results)
    first_player_wins = sum(result.first_player_won for result in results)

    for result in results:
        for player_result in result.player_results:
            stats[player_result.strategy].record_player(player_result)
        stats[result.winner_strategy].record_win(result.finish_round, result.ended_by_race)

    print("Solar Rush balance simulation")
    print(f"Games: {len(results)}")
    print(f"Players: {len(strategy_names)} ({', '.join(strategy_names)})")
    print(f"Seating: {'fixed' if fixed_seats else 'rotated'}")
    print(f"Race target from code: {RACE_TARGET_KW:.1f} kW")
    print(f"Max rounds: {MAX_ROUNDS}")
    print(f"Race finishes: {race_finishes / len(results):.1%}")
    print(f"First-player wins: {first_player_wins / len(results):.1%}")
    print()
    print("Strategy descriptions:")
    for name in dict.fromkeys(strategy_names):
        print(f"- {name}: {STRATEGIES[name].description}")
    print()
    print(
        "strategy      games  win%   race-win%  avg finish  p90 finish  "
        "avg output  avg units  avg bonus  avg proto"
    )
    print("-" * 98)

    for name in sorted(stats):
        item = stats[name]
        print(
            f"{name:<12} "
            f"{item.games:>5}  "
            f"{item.wins / item.games:>5.1%}  "
            f"{item.race_wins / max(1, item.wins):>9.1%}  "
            f"{mean(item.finish_rounds):>10.2f}  "
            f"{percentile(item.finish_rounds, 0.9):>10.0f}  "
            f"{mean(item.outputs):>10.2f}  "
            f"{mean(item.units):>9.2f}  "
            f"{mean(item.farm_bonuses):>9.2f}  "
            f"{mean(item.prototype_outputs):>9.2f}"
        )

    print()
    print("Wins by strategy:", ", ".join(f"{name}={winner_counts[name]}" for name in sorted(winner_counts)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", type=int, default=1000, help="number of games to simulate")
    parser.add_argument("--seed", type=int, default=1, help="base random seed")
    parser.add_argument(
        "--strategies",
        nargs="+",
        default=["rush", "balanced", "tech", "engineering"],
        choices=sorted(STRATEGIES),
        help="one strategy per player, 2-4 entries",
    )
    parser.add_argument(
        "--fixed-seats",
        action="store_true",
        help="keep strategies in the listed player order instead of rotating seats between games",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not 2 <= len(args.strategies) <= 4:
        raise SystemExit("--strategies must contain between 2 and 4 entries")

    results = []
    for idx in range(args.games):
        if args.fixed_seats:
            game_strategies = args.strategies
        else:
            offset = idx % len(args.strategies)
            game_strategies = args.strategies[offset:] + args.strategies[:offset]
        results.append(simulate_game(game_strategies, seed=args.seed + idx))
    print_report(results, args.strategies, args.fixed_seats)


if __name__ == "__main__":
    main()
