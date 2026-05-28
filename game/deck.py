import json
import os
import random
from dataclasses import dataclass, field

from game.card import Card


def _load_cards() -> list[Card]:
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cards.json')
    with open(path, encoding='utf-8') as f:
        raw = json.load(f)
    return [Card(**c) for c in raw]


@dataclass
class Deck:
    area: str
    draw_pile: list[Card] = field(default_factory=list)
    discard_pile: list[Card] = field(default_factory=list)

    def shuffle(self) -> None:
        random.shuffle(self.draw_pile)

    def draw(self) -> 'Card | None':
        if not self.draw_pile:
            if not self.discard_pile:
                return None
            self.draw_pile = self.discard_pile[:]
            self.discard_pile = []
            random.shuffle(self.draw_pile)
        return self.draw_pile.pop()

    def peek_top(self, n: int) -> list[Card]:
        """Return top n cards without removing them (top = last element)."""
        count = min(n, len(self.draw_pile))
        return list(reversed(self.draw_pile[-count:]))

    def take_top(self, n: int) -> list[Card]:
        """Remove and return top n cards."""
        count = min(n, len(self.draw_pile))
        taken = [self.draw_pile.pop() for _ in range(count)]
        return taken

    def put_to_bottom(self, cards: list[Card]) -> None:
        self.draw_pile = cards + self.draw_pile

    def discard(self, card: Card) -> None:
        self.discard_pile.append(card)

    def __len__(self) -> int:
        return len(self.draw_pile)


def build_decks() -> dict[str, Deck]:
    all_cards = _load_cards()
    decks: dict[str, Deck] = {}
    for area in ('material_science', 'chemistry', 'physics', 'engineering'):
        cards = [c for c in all_cards if c.area == area]
        deck = Deck(area=area, draw_pile=cards)
        deck.shuffle()
        decks[area] = deck
    return decks
