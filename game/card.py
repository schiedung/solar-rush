from dataclasses import dataclass
from typing import Any


AREAS = ('material_science', 'chemistry', 'physics', 'engineering')

CELL_TARGET_TYPES = (
    'upgrade_junction',
    'upgrade_optical',
    'upgrade_contact',
)

PLAYER_TARGET_TYPES = (
    'event_dust_storm',
    'event_grid_failure',
    'event_patent_block',
    'event_hail_damage',
    'event_regulatory',
)

IMMEDIATE_TYPES = (
    'upgrade_junction_all',
    'upgrade_optical_all',
    'upgrade_contact_all',
    'farm_multiplier',
    'event_policy_subsidy',
)


@dataclass
class Card:
    id: str
    area: str
    tier: int
    name: str
    description: str
    effect: dict[str, Any]

    def needs_cell_target(self) -> bool:
        return self.effect['type'] in CELL_TARGET_TYPES

    def needs_player_target(self) -> bool:
        return self.effect['type'] in PLAYER_TARGET_TYPES

    def is_immediate(self) -> bool:
        return self.effect['type'] in IMMEDIATE_TYPES

    def is_event(self) -> bool:
        return self.effect['type'].startswith('event_')
