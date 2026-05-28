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
        s.last_event_message = ''

        p.blocked_areas.clear()
        p.block_build = False

        s.actions_remaining = 2
        s.phase = Phase.ACTION

    def finish_turn(self) -> None:
        s = self.state
        p = s.current_player

        if p.halved_turns > 0:
            p.halved_turns -= 1

        if s.round_number >= MAX_ROUNDS and s.current_player_idx == len(s.players) - 1:
            winner = max(s.players, key=lambda pl: pl.total_output())
            s.winner = winner
            s.phase = Phase.GAME_OVER
        else:
            s.actions_remaining = 0
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
        return card

    # ── Play a card ───────────────────────────────────────────────────────────

    def select_card(self, card: Card) -> None:
        """Player clicks a card in hand. Slot cards apply instantly and are free; events need targeting."""
        s = self.state
        if s.phase != Phase.ACTION:
            return
        if card not in s.current_player.hand:
            return

        if card.is_immediate():
            if not card.is_slot_card() and s.actions_remaining <= 0:
                return
            self._apply_immediate(card)
        elif card.needs_player_target():
            if s.actions_remaining <= 0:
                return
            s.selected_card = card
            s.phase = Phase.TARGETING_PLAYER

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
            target.block_build = True
            s.last_event_message = f'Grid Failure hits {target.name} — cannot Build next turn!'
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
        return True

    # ── Build ─────────────────────────────────────────────────────────────────

    def perform_build(self) -> bool:
        """Build a unit from the current prototype output. Freezes that kW as score."""
        s = self.state
        if s.phase != Phase.ACTION or s.actions_remaining <= 0:
            return False
        p = s.current_player
        if p.block_build:
            s.last_event_message = f'{p.name}: Grid Failure active — cannot Build this turn!'
            return False
        kwh = p.build_unit()
        s.last_event_message = (
            f'{p.name} built a unit: {kwh:.2f} kW  '
            f'(total output now {p.total_output():.2f} kW)'
        )
        s.actions_remaining -= 1

        winner = s.check_win(s.current_player)
        if winner:
            s.winner = s.current_player
            s.phase = Phase.GAME_OVER
            return True

        return True

    # ── Pass ──────────────────────────────────────────────────────────────────

    def perform_pass(self) -> bool:
        s = self.state
        if s.phase != Phase.ACTION or s.actions_remaining <= 0:
            return False
        s.actions_remaining -= 1
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
        return True

    # ── Unslot ────────────────────────────────────────────────────────────────

    def perform_unslot(self, slot_key: str) -> bool:
        """Return a prototype card to hand. Free — costs no actions."""
        s = self.state
        p = s.current_player
        attr = f'{slot_key}_card'
        card = getattr(p.prototype, attr, None)
        if card is None:
            return False
        setattr(p.prototype, attr, None)
        p.hand.append(card)
        return True

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _apply_immediate(self, card: Card) -> None:
        s = self.state
        p = s.current_player
        etype = card.effect['type']

        p.hand.remove(card)

        if etype in ('set_junction', 'set_optical', 'set_contact'):
            old = p.prototype.slot_card(card)
            if old:
                p.hand.append(old)  # displaced card returns to hand, not discard
            # slot cards are free — no action cost, no actions_done check
            return
        elif etype == 'farm_multiplier':
            p.farm_bonus += card.effect['delta']
            s.decks[card.area].discard(card)
        elif etype == 'event_policy_subsidy':
            for area in ('material_science', 'chemistry', 'physics', 'engineering'):
                extra = s.decks[area].draw()
                if extra:
                    p.hand.append(extra)
            s.last_event_message = f'{p.name} draws extra cards!'
            s.decks[card.area].discard(card)

        s.actions_remaining -= 1

    
