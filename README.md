# Solar Rush

A competitive card-driven board game for 2–4 players. Research real solar cell technologies, upgrade your prototype, and build a farm that outpaces your rivals.

Built with Python + Pygame.

---

## Goal

Be the first player to reach **20 kW of total farm output** — or have the highest output when 20 rounds run out.

---

## How to play

### Your turn

You have **2 actions** per turn. Spend them however you like:

| Action | Cost |
|---|---|
| Draw a card from a research deck | 1 action |
| Build a unit from your prototype | 1 action |
| Research (peek 3 cards, keep 1) | 2 actions |
| Play an event card on an opponent | 1 action |
| Pass | 1 action |

**Slotting and unslotting prototype cards is always free** — swap them around as much as you want before spending actions.

### The prototype

Your prototype is the engine of your farm. It has three upgrade slots, each tied to a research discipline:

| Slot | Discipline | Real technology |
|---|---|---|
| Junction | Material Science | Semiconductor absorber layer |
| Optical | Chemistry | Anti-reflection / passivation coating |
| Contact | Physics | Contact grid architecture |

Each slot can hold one research card. The prototype's output is the **product** of all three slots' multipliers — a good junction, coating, and contact together multiply each other.

**Tiers and multipliers:**

| Junction | ×mult | Optical | ×mult | Contact | ×mult |
|---|---|---|---|---|---|
| Poly-Si | ×1.0 | Bare Surface | ×1.00 | Al-BSF | ×1.0 |
| Mono-Si | ×1.3 | Basic ARC | ×1.15 | PERC | ×1.2 |
| CIGS | ×1.6 | SiNx | ×1.30 | Bifacial | ×1.4 |
| Perovskite | ×2.0 | Al₂O₃ | ×1.45 | HJT | ×1.6 |
| GaAs Multi-Jct | ×2.8 | Advanced Stack | ×1.65 | IBC | ×1.9 |

A fully upgraded prototype outputs **2.8 × 1.65 × 1.9 ≈ 8.77 kWh** per unit built.

### Building units

When you Build, the prototype's current output is **frozen** as a permanent unit in your farm. That value never changes, even if you later upgrade the prototype. Build early to start accumulating output; build late for higher-value units.

Your farm's total output = sum of all built units (modified by bonuses and active effects).

### Engineering cards

The Engineering deck contains two special card types:

- **Farm Multiplier** — immediately applies a permanent bonus to all your farm output (+10–20%)
- **Event cards** — played on an opponent to sabotage their farm

### Event cards

| Event | Effect |
|---|---|
| Dust Storm | Target's output is halved for one turn |
| Grid Failure | Target cannot Build on their next turn |
| Patent Block | Randomly blocks one of target's research decks for one turn |
| Hail Damage | Destroys target's most recently built unit |
| Regulatory Change | Target discards their top hand card |
| Policy Subsidy | (Immediate, self) Draw an extra card from each deck |

---

## Installation

**Requirements:** Python 3.12+, Pygame 2.x

```bash
pip install pygame
python main.py
```

---

## Controls

| Input | Action |
|---|---|
| Left click | Select / confirm |
| Right click | Deselect / cancel |
| Escape | Cancel current selection |
| F11 | Toggle fullscreen |
| Alt+F4 | Quit |

---

## Project structure

```
solar-rush/
├── main.py          Entry point
├── data/
│   ├── cards.json       All 100 cards
│   └── cell_parts.json  Tier definitions for the prototype parts
├── assets/
│   └── manifest.json    Image asset registry
├── game/            Game logic (no Pygame dependency)
└── ui/              Rendering and layout
```

To add card artwork, drop PNGs into `assets/` and register them in `assets/manifest.json` using the key `card_<card_id>` (e.g. `"card_ms_01": "czochralski.png"`).
