import json
import os
from dataclasses import dataclass, field

_data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cell_parts.json')
with open(_data_path, encoding='utf-8') as _f:
    _CELL_PARTS = json.load(_f)

JUNCTION_TIERS = _CELL_PARTS['junction']['tiers']
OPTICAL_TIERS  = _CELL_PARTS['optical']['tiers']
CONTACT_TIERS  = _CELL_PARTS['contact']['tiers']

MAX_TIER = len(JUNCTION_TIERS) - 1  # 4


@dataclass
class SolarCell:
    junction_tier: int = 0
    optical_tier:  int = 0
    contact_tier:  int = 0

    def kwh_output(self) -> float:
        j = JUNCTION_TIERS[self.junction_tier]['multiplier']
        o = OPTICAL_TIERS[self.optical_tier]['multiplier']
        c = CONTACT_TIERS[self.contact_tier]['multiplier']
        return j * o * c

    def upgrade_junction(self, delta: int) -> None:
        self.junction_tier = min(MAX_TIER, self.junction_tier + delta)

    def upgrade_optical(self, delta: int) -> None:
        self.optical_tier = min(MAX_TIER, self.optical_tier + delta)

    def upgrade_contact(self, delta: int) -> None:
        self.contact_tier = min(MAX_TIER, self.contact_tier + delta)

    def part_names(self) -> dict[str, str]:
        return {
            'junction': JUNCTION_TIERS[self.junction_tier]['name'],
            'optical':  OPTICAL_TIERS[self.optical_tier]['name'],
            'contact':  CONTACT_TIERS[self.contact_tier]['name'],
        }
