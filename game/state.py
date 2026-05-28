from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from game.card import Card
from game.deck import Deck
from game.player import Player


RACE_TARGET_KW = 20.0
MAX_ROUNDS = 20

PLAYER_COLORS = [
    (220, 80,  80),   # Red
    (80,  170, 230),  # Blue
    (80,  200, 100),  # Green
    (240, 190, 50),   # Yellow
]


class Phase(Enum):
    ACTION             = auto()
    TARGETING_CELL     = auto()  # unused — kept for future use
    TARGETING_PLAYER   = auto()  # event card selected, waiting for player click
    RESEARCH_PICK_AREA = auto()  # player clicked Research, now pick a deck
    RESEARCH_CHOOSE    = auto()  # 3 cards revealed, player picks 1
    HANDOFF            = auto()  # "Pass to Player X" screen
    GAME_OVER          = auto()


@dataclass
class GameState:
    players: list[Player]
    decks: dict[str, Deck]
    round_number: int = 1
    current_player_idx: int = 0
    actions_remaining: int = 2
    phase: Phase = Phase.ACTION
    winner: Optional[Player] = None
    selected_card: Optional[Card] = None
    research_choices: list[Card] = field(default_factory=list)
    research_area: str = ''
    last_event_message: str = ''

    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_idx]

    def opponent_indices(self) -> list[int]:
        return [i for i in range(len(self.players)) if i != self.current_player_idx]

    def check_win(self) -> Optional[Player]:
        for p in self.players:
            if p.total_output() >= RACE_TARGET_KW:
                return p
        return None


def make_game(num_players: int) -> GameState:
    from game.deck import build_decks
    players = [
        Player(name=f'Player {i+1}', color=PLAYER_COLORS[i])
        for i in range(num_players)
    ]
    return GameState(players=players, decks=build_decks())
