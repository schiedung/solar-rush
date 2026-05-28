import json
import os
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from game.card import Card

_data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cell_parts.json')
with open(_data_path, encoding='utf-8') as _f:
    _CELL_PARTS = json.load(_f)

JUNCTION_TIERS = _CELL_PARTS['junction']['tiers']
OPTICAL_TIERS  = _CELL_PARTS['optical']['tiers']
CONTACT_TIERS  = _CELL_PARTS['contact']['tiers']

MAX_TIER = len(JUNCTION_TIERS) - 1  # 4

SLOT_AREA = {
    'set_junction': 'material_science',
    'set_optical':  'chemistry',
    'set_contact':  'physics',
}

SLOT_LABEL = {
    'junction': 'Junction',
    'optical':  'Optical',
    'contact':  'Contact',
}


class Prototype:
    """
    The player's research cell. Holds one card per slot (junction / optical / contact).
    When a new card is slotted it displaces the previous one, which is returned for discarding.
    Building a unit snapshots the current output as a frozen VP value.
    """

    def __init__(self) -> None:
        self.junction_card: Optional['Card'] = None
        self.optical_card:  Optional['Card'] = None
        self.contact_card:  Optional['Card'] = None

    # ── Tier accessors ───────────────────────────────────────────────────────

    def junction_tier(self) -> int:
        return self.junction_card.effect['to_tier'] if self.junction_card else 0

    def optical_tier(self) -> int:
        return self.optical_card.effect['to_tier'] if self.optical_card else 0

    def contact_tier(self) -> int:
        return self.contact_card.effect['to_tier'] if self.contact_card else 0

    # ── Output ───────────────────────────────────────────────────────────────

    def kwh_output(self) -> float:
        j = JUNCTION_TIERS[self.junction_tier()]['multiplier']
        o = OPTICAL_TIERS[self.optical_tier()]['multiplier']
        c = CONTACT_TIERS[self.contact_tier()]['multiplier']
        return j * o * c

    # ── Slot a card ──────────────────────────────────────────────────────────

    def slot_card(self, card: 'Card') -> Optional['Card']:
        """
        Insert card into its slot. Returns the displaced card (if any) for discarding.
        The slotted card stays in the prototype; caller must NOT discard it.
        """
        etype = card.effect['type']
        if etype == 'set_junction':
            old, self.junction_card = self.junction_card, card
        elif etype == 'set_optical':
            old, self.optical_card = self.optical_card, card
        elif etype == 'set_contact':
            old, self.contact_card = self.contact_card, card
        else:
            return None
        return old

    # ── Helpers ──────────────────────────────────────────────────────────────

    def active_cards(self) -> list['Card']:
        return [c for c in (self.junction_card, self.optical_card, self.contact_card) if c]

    def part_names(self) -> dict[str, str]:
        return {
            'junction': JUNCTION_TIERS[self.junction_tier()]['name'],
            'optical':  OPTICAL_TIERS[self.optical_tier()]['name'],
            'contact':  CONTACT_TIERS[self.contact_tier()]['name'],
        }

    def part_multipliers(self) -> dict[str, float]:
        return {
            'junction': JUNCTION_TIERS[self.junction_tier()]['multiplier'],
            'optical':  OPTICAL_TIERS[self.optical_tier()]['multiplier'],
            'contact':  CONTACT_TIERS[self.contact_tier()]['multiplier'],
        }
