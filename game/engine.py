import random
from typing import Optional

from game.card import Card
from game.cell import SolarCell
from game.player import Player
from game.state import GameState, Phase, MAX_ROUNDS


class TurnEngine:
    def __init__(self, state: GameState) -> None:
        self.state = state

    # ── Phase transitions ────────────────────────────────────────────────────

    def begin_turn(self) -> None:
        """Called at the start of each player's turn (score phase)."""
        s = self.state
        p = s.current_player
        s.phase = Phase.SCORE
        s.last_event_message = ''

        # Tick timed effects
        if p.halved_turns > 0:
            p.halved_turns -= 1

        # Clear expired blocks
        p.blocked_areas.clear()

        if p.skip_score:
            p.skip_score = False
            s.last_event_message = f'{p.name} grid failure — score skipped!'
        else:
            earned = p.total_output()
            p.banked_kwh += earned
            s.last_event_message = f'{p.name} earned {earned:.1f} kWh'

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
            # Last player of last round — game ends by round limit
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

    # ── Actions ──────────────────────────────────────────────────────────────

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

    def select_card(self, card: Card) -> None:
        """Player clicks a card in hand — enters targeting phase if needed."""
        s = self.state
        if s.phase != Phase.ACTION or s.actions_remaining <= 0:
            return
        if card not in s.current_player.hand:
            return
        s.selected_card = card
        if card.needs_cell_target():
            s.phase = Phase.TARGETING_CELL
        elif card.needs_player_target():
            s.phase = Phase.TARGETING_PLAYER
        else:
            # Immediate card — resolve now
            self._apply_immediate(card)
            s.selected_card = None

    def deselect_card(self) -> None:
        s = self.state
        if s.phase in (Phase.TARGETING_CELL, Phase.TARGETING_PLAYER, Phase.RESEARCH_PICK_AREA):
            s.selected_card = None
            s.phase = Phase.ACTION

    def enter_research_mode(self) -> bool:
        s = self.state
        if s.phase != Phase.ACTION or s.actions_remaining < 2:
            return False
        s.phase = Phase.RESEARCH_PICK_AREA
        return True

    def perform_play_upgrade(self, cell_idx: int) -> bool:
        s = self.state
        if s.phase != Phase.TARGETING_CELL or not s.selected_card:
            return False
        p = s.current_player
        if cell_idx < 0 or cell_idx >= len(p.farm):
            return False

        card = s.selected_card
        cell = p.farm[cell_idx]
        etype = card.effect['type']
        delta = card.effect['delta']

        if etype == 'upgrade_junction':
            cell.upgrade_junction(delta)
        elif etype == 'upgrade_optical':
            cell.upgrade_optical(delta)
        elif etype == 'upgrade_contact':
            cell.upgrade_contact(delta)

        p.hand.remove(card)
        s.decks[card.area].discard(card)
        s.selected_card = None
        s.actions_remaining -= 1
        s.phase = Phase.ACTION
        self._check_actions_done()
        return True

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
                s.last_event_message = f'Patent Block: {target.name} loses {blocked.replace("_"," ").title()}!'
        elif etype == 'event_hail_damage':
            if len(target.farm) > 1:
                target.farm.pop()
                s.last_event_message = f'Hail Damage! {target.name} loses a cell!'
            else:
                s.last_event_message = f'Hail Damage fizzles — {target.name} only has 1 cell.'
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

    def perform_build(self) -> bool:
        s = self.state
        if s.phase != Phase.ACTION or s.actions_remaining <= 0:
            return False
        s.current_player.farm.append(SolarCell())
        s.actions_remaining -= 1
        self._check_actions_done()
        return True

    def perform_pass(self) -> bool:
        """Spend 1 action doing nothing."""
        s = self.state
        if s.phase != Phase.ACTION or s.actions_remaining <= 0:
            return False
        s.actions_remaining -= 1
        self._check_actions_done()
        return True

    def start_research(self, area: str) -> bool:
        """Spend 2 actions to peek top 3 cards from a deck."""
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

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _apply_immediate(self, card: Card) -> None:
        s = self.state
        p = s.current_player
        etype = card.effect['type']

        if etype in ('upgrade_junction_all', 'upgrade_optical_all', 'upgrade_contact_all'):
            delta = card.effect['delta']
            for cell in p.farm:
                if etype == 'upgrade_junction_all':
                    cell.upgrade_junction(delta)
                elif etype == 'upgrade_optical_all':
                    cell.upgrade_optical(delta)
                elif etype == 'upgrade_contact_all':
                    cell.upgrade_contact(delta)
        elif etype == 'farm_multiplier':
            p.farm_bonus += card.effect['delta']
        elif etype == 'event_policy_subsidy':
            for area_order in ('material_science', 'chemistry', 'physics', 'engineering'):
                if len(p.hand) < p.HAND_LIMIT + 2:
                    extra = s.decks[area_order].draw()
                    if extra:
                        p.hand.append(extra)
            s.last_event_message = f'{p.name} draws 2 extra cards!'

        p.hand.remove(card)
        s.decks[card.area].discard(card)
        s.actions_remaining -= 1
        self._check_actions_done()

    def _check_actions_done(self) -> None:
        s = self.state
        if s.phase == Phase.ACTION and s.actions_remaining <= 0:
            self.begin_discard_phase()
