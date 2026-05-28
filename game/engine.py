import random
from typing import Optional

from game.card import Card
from game.player import Player
from game.state import GameState, Phase, MAX_ROUNDS


class TurnEngine:
    def __init__(self, state: GameState) -> None:
        self.state = state

    # ── Phase transitions ────────────────────────────────────────────────────

    def begin_turn(self) -> None:
        s = self.state
        p = s.current_player
        s.phase = Phase.SCORE
        s.last_event_message = ''

        if p.halved_turns > 0:
            p.halved_turns -= 1

        p.blocked_areas.clear()

        if p.skip_score:
            p.skip_score = False
            s.last_event_message = f'{p.name}: grid failure — score skipped!'
        else:
            earned = p.total_output()
            p.banked_kwh += earned
            if earned > 0:
                s.last_event_message = f'{p.name} earned {earned:.2f} kWh  ({len(p.units)} units)'
            else:
                s.last_event_message = f'{p.name} has no built units yet — build one!'

        winner = s.check_win()
        if winner:
            s.winner = winner
            s.phase = Phase.GAME_OVER
            return

        s.actions_remaining = 2
        s.phase = Phase.ACTION

    def begin_discard_phase(self) -> None:
        s = self.state
        if len(s.current_player.hand) > s.current_player.HAND_LIMIT:
            s.phase = Phase.DISCARD
        else:
            self._begin_handoff()

    def _begin_handoff(self) -> None:
        s = self.state
        if s.round_number >= MAX_ROUNDS and s.current_player_idx == len(s.players) - 1:
            winner = max(s.players, key=lambda p: p.banked_kwh)
            s.winner = winner
            s.phase = Phase.GAME_OVER
        else:
            s.phase = Phase.HANDOFF

    def advance_to_next_player(self) -> None:
        s = self.state
        s.selected_card = None
        s.research_choices = []
        next_idx = (s.current_player_idx + 1) % len(s.players)
        if next_idx == 0:
            s.round_number += 1
        s.current_player_idx = next_idx
        self.begin_turn()

    # ── Draw ─────────────────────────────────────────────────────────────────

    def can_draw(self, area: str) -> bool:
        s = self.state
        return (
            s.phase == Phase.ACTION
            and s.actions_remaining > 0
            and area not in s.current_player.blocked_areas
            and len(s.decks[area]) > 0
        )

    def perform_draw(self, area: str) -> Optional[Card]:
        s = self.state
        if not self.can_draw(area):
            return None
        card = s.decks[area].draw()
        if card:
            s.current_player.hand.append(card)
            s.actions_remaining -= 1
            self._check_actions_done()
        return card

    # ── Play a card ───────────────────────────────────────────────────────────

    def select_card(self, card: Card) -> None:
        """Player clicks a card in hand. Immediate cards apply instantly; events need targeting."""
        s = self.state
        if s.phase != Phase.ACTION or s.actions_remaining <= 0:
            return
        if card not in s.current_player.hand:
            return

        if card.is_immediate():
            self._apply_immediate(card)
        elif card.needs_player_target():
            s.selected_card = card
            s.phase = Phase.TARGETING_PLAYER
        # (no TARGETING_CELL phase needed — all slot cards are immediate)

    def deselect_card(self) -> None:
        s = self.state
        if s.phase in (Phase.TARGETING_PLAYER, Phase.RESEARCH_PICK_AREA):
            s.selected_card = None
            s.phase = Phase.ACTION

    def perform_play_event(self, target_player_idx: int) -> bool:
        s = self.state
        if s.phase != Phase.TARGETING_PLAYER or not s.selected_card:
            return False
        if target_player_idx == s.current_player_idx:
            return False

        card = s.selected_card
        target = s.players[target_player_idx]
        etype = card.effect['type']

        if etype == 'event_dust_storm':
            target.halved_turns = 1
            s.last_event_message = f'Dust Storm hits {target.name}!'
        elif etype == 'event_grid_failure':
            target.skip_score = True
            s.last_event_message = f'Grid Failure hits {target.name}!'
        elif etype == 'event_patent_block':
            available = [a for a in ('material_science', 'chemistry', 'physics', 'engineering')
                         if a not in target.blocked_areas]
            if available:
                blocked = random.choice(available)
                target.blocked_areas.add(blocked)
                s.last_event_message = (
                    f'Patent Block: {target.name} loses '
                    f'{blocked.replace("_", " ").title()}!'
                )
        elif etype == 'event_hail_damage':
            if target.units:
                target.units.pop()
                s.last_event_message = f'Hail Damage! {target.name} loses a built unit!'
            else:
                s.last_event_message = f'Hail Damage fizzles — {target.name} has no units.'
        elif etype == 'event_regulatory':
            discarded = target.discard_top_hand_card()
            if discarded:
                s.decks[discarded.area].discard(discarded)
                s.last_event_message = f'Regulatory Change: {target.name} discards {discarded.name}!'
            else:
                s.last_event_message = f'Regulatory Change fizzles — {target.name} has no cards.'

        s.current_player.hand.remove(card)
        s.decks[card.area].discard(card)
        s.selected_card = None
        s.actions_remaining -= 1
        s.phase = Phase.ACTION
        self._check_actions_done()
        return True

    # ── Build ─────────────────────────────────────────────────────────────────

    def perform_build(self) -> bool:
        """Build a unit from the current prototype output. Freezes that kWh as VP."""
        s = self.state
        if s.phase != Phase.ACTION or s.actions_remaining <= 0:
            return False
        kwh = s.current_player.build_unit()
        s.last_event_message = (
            f'{s.current_player.name} built a unit: {kwh:.2f} kWh  '
            f'(prototype output locked in)'
        )
        s.actions_remaining -= 1
        self._check_actions_done()
        return True

    # ── Pass ──────────────────────────────────────────────────────────────────

    def perform_pass(self) -> bool:
        s = self.state
        if s.phase != Phase.ACTION or s.actions_remaining <= 0:
            return False
        s.actions_remaining -= 1
        self._check_actions_done()
        return True

    # ── Research ──────────────────────────────────────────────────────────────

    def enter_research_mode(self) -> bool:
        s = self.state
        if s.phase != Phase.ACTION or s.actions_remaining < 2:
            return False
        s.phase = Phase.RESEARCH_PICK_AREA
        return True

    def start_research(self, area: str) -> bool:
        s = self.state
        if s.phase != Phase.RESEARCH_PICK_AREA:
            return False
        if s.actions_remaining < 2:
            return False
        if area in s.current_player.blocked_areas:
            return False
        if len(s.decks[area]) == 0:
            return False
        cards = s.decks[area].take_top(3)
        if not cards:
            return False
        s.research_choices = cards
        s.research_area = area
        s.actions_remaining -= 2
        s.phase = Phase.RESEARCH_CHOOSE
        return True

    def complete_research(self, choice_idx: int) -> bool:
        s = self.state
        if s.phase != Phase.RESEARCH_CHOOSE:
            return False
        if choice_idx < 0 or choice_idx >= len(s.research_choices):
            return False
        chosen = s.research_choices[choice_idx]
        rest = [c for i, c in enumerate(s.research_choices) if i != choice_idx]
        s.current_player.hand.append(chosen)
        s.decks[s.research_area].put_to_bottom(rest)
        s.research_choices = []
        s.phase = Phase.ACTION
        self._check_actions_done()
        return True

    # ── Discard ───────────────────────────────────────────────────────────────

    def perform_discard(self, card_idx: int) -> bool:
        s = self.state
        if s.phase != Phase.DISCARD:
            return False
        p = s.current_player
        if card_idx < 0 or card_idx >= len(p.hand):
            return False
        card = p.hand.pop(card_idx)
        s.decks[card.area].discard(card)
        if len(p.hand) <= p.HAND_LIMIT:
            self._begin_handoff()
        return True

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _apply_immediate(self, card: Card) -> None:
        s = self.state
        p = s.current_player
        etype = card.effect['type']

        p.hand.remove(card)  # remove from hand first

        if etype in ('set_junction', 'set_optical', 'set_contact'):
            old = p.prototype.slot_card(card)
            if old:
                s.decks[old.area].discard(old)
            # card now lives in the prototype slot; do NOT discard it
        elif etype == 'farm_multiplier':
            p.farm_bonus += card.effect['delta']
            s.decks[card.area].discard(card)
        elif etype == 'event_policy_subsidy':
            for area in ('material_science', 'chemistry', 'physics', 'engineering'):
                if len(p.hand) < p.HAND_LIMIT + 2:
                    extra = s.decks[area].draw()
                    if extra:
                        p.hand.append(extra)
            s.last_event_message = f'{p.name} draws 2 extra cards!'
            s.decks[card.area].discard(card)

        s.actions_remaining -= 1
        self._check_actions_done()

    def _check_actions_done(self) -> None:
        s = self.state
        if s.phase == Phase.ACTION and s.actions_remaining <= 0:
            self.begin_discard_phase()
