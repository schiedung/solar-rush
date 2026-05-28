# Solar Rush — AGENTS.md

Reference document for LLM agents working on this codebase. Read this before editing any file.

---

## What the game is

**Solar Rush** is a competitive hot-seat board game for 2–4 players, implemented in Python 3.12 + Pygame 2.x. Players race to be first to reach **20 kW of output**, or to have the highest output after 20 rounds.

Each player owns a **prototype solar cell** with three upgrade slots and a **farm** of frozen built units. On each turn a player takes 2 actions, then passes to the next player.

**Win condition:** `player.total_output() >= 20.0` (checked immediately after any Build action) or highest `total_output()` when round 20 ends.

---

## Core concepts

### Prototype cell

Every player has one `Prototype` (in `game/cell.py`). It has three card slots:

| Slot | Research area | Real technology |
|---|---|---|
| `junction_card` | Material Science | Semiconductor junction |
| `optical_card` | Chemistry | Anti-reflection / passivation layer |
| `contact_card` | Physics | Contact grid architecture |

Each slot holds one `Card` or `None`. The prototype's kW output is the **product** of all three slots' multipliers:

```
kwh_output() = junction_multiplier × optical_multiplier × contact_multiplier
```

Tier data (names and multipliers) live in `data/cell_parts.json`. Tiers 0–4 per slot, where tier 0 = no card slotted (multiplier 1.0).

### Built units

When a player takes the **Build** action, `player.build_unit()` snapshots `prototype.kwh_output()` as a float and appends it to `player.units`. That value is frozen — upgrading the prototype later does not change existing units.

`player.total_output()` = `sum(units) × (1 + farm_bonus)`, halved if `halved_turns > 0`.

### Scoring

Score at any moment = `player.total_output()`. There is no per-turn accumulation. The scoreboard and progress track always reflect the live value.

### Actions

A turn starts with `actions_remaining = 2`. Each turn the current player may spend actions:

| Action | Cost | Notes |
|---|---|---|
| **Draw** from a deck | 1 action | Card goes to hand |
| **Build** a unit | 1 action | Snapshots prototype output; triggers win check |
| **Research** | 2 actions | Peek 3 cards from a chosen deck, keep 1 |
| **Pass** | 1 action | Skips one action |
| **Play an event card** | 1 action | Targets another player |
| **Slot a card** | **0 actions** | Free; displaced card returns to hand |
| **Unslot a card** | **0 actions** | Free; card returns to hand |

When `actions_remaining` hits 0 the game transitions to `HANDOFF`.

### Decks

There are four shared decks, one per research area, each 25 cards. Decks cycle (discard reshuffles back when exhausted). Cards are never permanently removed from the game.

---

## Card types

Defined in `game/card.py`. The `effect` dict on each card has a `type` key:

| Effect type | Behaviour |
|---|---|
| `set_junction` | Free; slots into prototype's junction slot |
| `set_optical` | Free; slots into prototype's optical slot |
| `set_contact` | Free; slots into prototype's contact slot |
| `farm_multiplier` | Immediate; adds `effect['delta']` to `player.farm_bonus`; consumed |
| `event_policy_subsidy` | Immediate; draws 1 extra card per deck; consumed |
| `event_dust_storm` | Targets opponent; halves their output for 1 turn |
| `event_grid_failure` | Targets opponent; sets `block_build = True` for 1 turn |
| `event_patent_block` | Targets opponent; randomly blocks one of their research areas |
| `event_hail_damage` | Targets opponent; removes their most recently built unit |
| `event_regulatory` | Targets opponent; discards their top hand card |

Slot cards (`set_*`) are **free and immediate** — they cost no actions and are applied the moment the player clicks them. The displaced card (if any) returns to the player's hand. `farm_multiplier` and `event_policy_subsidy` are also immediate but do cost 1 action.

---

## Phase state machine

Defined in `game/state.py` as `Phase(Enum)`.

```
ACTION
  │
  ├─ click deck button        → ACTION (card added to hand, actions -= 1)
  ├─ click slot card in hand  → ACTION (free, no action cost)
  ├─ click event card in hand → TARGETING_PLAYER → ACTION (actions -= 1)
  ├─ click Research button    → RESEARCH_PICK_AREA
  │                               └─ click deck → RESEARCH_CHOOSE
  │                                                 └─ click card → ACTION
  ├─ click Build / Pass       → ACTION (actions -= 1)
  └─ actions_remaining == 0   → HANDOFF
                                  └─ click Continue → ACTION (next player)
```

`GAME_OVER` is entered from any state where `check_win()` returns a player, or when round 20 ends and all players have taken their final turn.

---

## File map

```
SoestSciGame/
├── main.py                   Entry point, event loop, fullscreen logic
├── data/
│   ├── cards.json            All 100 cards (25 × 4 areas)
│   └── cell_parts.json       Tier names and multipliers for 3 prototype parts
├── assets/
│   └── manifest.json         Maps logical asset names → file paths (null = placeholder)
├── game/
│   ├── card.py               Card dataclass + effect-type constants
│   ├── cell.py               Prototype class; kwh_output(); slot_card()
│   ├── deck.py               Deck dataclass; draw/discard/research helpers
│   ├── player.py             Player dataclass; total_output(); build_unit()
│   ├── state.py              GameState dataclass; Phase enum; check_win(); make_game()
│   └── engine.py             TurnEngine; all legal actions; phase transitions
└── ui/
    ├── colors.py             Solarized Dark palette + semantic aliases
    ├── fonts.py              Font cache (Segoe UI, 7 sizes)
    ├── assets.py             Image loader with placeholder fallback
    ├── layout.py             All pixel constants; helper rect functions
    ├── renderer.py           Top-level draw(); assembles UIRects for click dispatch
    ├── progress_track.py     Top bar: rail, player tokens, round/action info
    ├── farm_view.py          Left panel: prototype slots + built units grid; returns slot_rects
    ├── deck_panel.py         Right panel: deck buttons + action buttons + scoreboard
    ├── hand_view.py          Bottom bar: player's hand cards
    └── event_overlay.py      Modal overlays: handoff, game over, research choose, target player
```

---

## Key data flows

### Click dispatch

`main.py:handle_click()` receives a **logical-coordinate** position (already scaled from screen coords by `_scale_mouse()`). It checks `state.phase`, then hits rects returned by the previous `R.draw()` call stored in `rects: UIRects`.

`UIRects` (defined in `ui/renderer.py`) carries:
- `hand_rects` — one rect per card in current player's hand, in hand order
- `slot_rects` — `dict[slot_key, unslot_btn_rect]` for filled prototype slots
- `research_rects` — rects for the 3-card research overlay
- `player_target_rects` — one rect per player (self-slot is a zero-size placeholder)
- `handoff_btn`, `play_again_btn` — overlay confirm buttons

### Rendering pipeline

Every frame:
1. `R.draw(logical_surf, state, mouse_pos)` fills `logical_surf` (1280×720).
2. `pygame.transform.scale(logical_surf, screen.get_size(), screen)` scales to the actual window.
3. Mouse positions from events are passed through `_scale_mouse()` before any rect check.

The logical surface is always 1280×720 regardless of window size or fullscreen state.

### Prototype slot cards and ownership

Cards in prototype slots are **not** in any deck's discard pile. They are owned by the `Prototype` object. When a card is slotted, the displaced card goes to `player.hand`. When a player unslots via the ↩ button, the card returns to `player.hand`. Cards are only returned to decks when they are explicitly discarded (event cards after use, `farm_multiplier`, `event_policy_subsidy`).

---

## Invariants to preserve

- `player.total_output()` is the authoritative score. Never read or write `banked_kwh` — it does not exist.
- Slot cards (`set_junction/optical/contact`) must never decrement `actions_remaining` and must never call `_check_actions_done()`. They are free.
- After every action that could end the turn (`perform_build`, `perform_pass`, `perform_draw`, `perform_play_event`, `complete_research`), call `_check_actions_done()` (via `engine`). `perform_build` additionally calls `check_win()` before that.
- `_scale_mouse()` must be applied to every `event.pos` and to `pygame.mouse.get_pos()` before passing to any rect collision check or to `R.draw()`.
- `Phase.DISCARD` and `Phase.SCORE` do not exist. There is no hand limit. Do not add them back.

---

## Extending the game

### Adding a new card effect type

1. Add the effect type string to the appropriate tuple in `game/card.py` (`IMMEDIATE_TYPES` or `PLAYER_TARGET_TYPES`).
2. Handle it in `game/engine.py`: immediate effects go in `_apply_immediate()`; player-targeted effects go in `perform_play_event()`.
3. Add entries to `data/cards.json` with the new `effect.type`.

### Adding a new card image

Drop a PNG into `assets/` and add an entry to `assets/manifest.json`:
```json
"card_ms_01": "my_image.png"
```
The key format for card images is `card_<card_id>`. `ui/assets.py:get_card_image()` handles loading with placeholder fallback.

### Changing layout

All pixel constants are in `ui/layout.py`. The logical canvas is fixed at 1280×720 (`SW × SH`). Do not hard-code pixel values in rendering files — reference `L.*` constants.

### Changing colors

All colors are in `ui/colors.py`. The palette is Solarized Dark. Semantic aliases (`TEXT_MAIN`, `BTN_NORMAL`, `AREA`, etc.) are what rendering code uses; change only those aliases to retheme without touching rendering files.
