import pygame

SW, SH = 1280, 720

TOPBAR_H = 110
MAIN_H   = 410    # SH - TOPBAR_H - HAND_H
HAND_H   = 200
FARM_W   = 920
PANEL_W  = SW - FARM_W

# Progress track geometry
TRACK_X0 = 48
TRACK_X1 = 1232
TRACK_Y  = 44    # rail y (absolute screen y)
TRACK_USABLE = TRACK_X1 - TRACK_X0  # 1184
TOKEN_R = 14

# Deck buttons (2×2 inside the painted right panel)
_DW, _DH = 150, 74
_DX0 = 944
_DY0 = 138
_DGAP = 10
DECK_RECTS: dict[str, pygame.Rect] = {
    'material_science': pygame.Rect(_DX0,            _DY0,            _DW, _DH),
    'chemistry':        pygame.Rect(_DX0 + _DW + _DGAP, _DY0,         _DW, _DH),
    'physics':          pygame.Rect(_DX0,            _DY0 + _DH + _DGAP, _DW, _DH),
    'engineering':      pygame.Rect(_DX0 + _DW + _DGAP, _DY0 + _DH + _DGAP, _DW, _DH),
}

# Action buttons
ACTION_X   = 944
ACTION_Y   = 318
ACTION_BTN_W = 150
ACTION_BTN_H = 44
ACTION_GAP   = 6
BUILD_BTN    = pygame.Rect(ACTION_X,                     ACTION_Y, ACTION_BTN_W, ACTION_BTN_H)
RESEARCH_BTN = pygame.Rect(ACTION_X + ACTION_BTN_W + _DGAP, ACTION_Y, ACTION_BTN_W, ACTION_BTN_H)
PASS_BTN        = pygame.Rect(ACTION_X,                          ACTION_Y + ACTION_BTN_H + ACTION_GAP, ACTION_BTN_W, ACTION_BTN_H)
FINISH_TURN_BTN = pygame.Rect(ACTION_X + ACTION_BTN_W + _DGAP,  ACTION_Y + ACTION_BTN_H + ACTION_GAP, ACTION_BTN_W, ACTION_BTN_H)

# Below action buttons
STATUS_TEXT_Y    = ACTION_Y + 2 * (ACTION_BTN_H + ACTION_GAP) + 8
SCOREBOARD_Y     = STATUS_TEXT_Y + 22

# Handoff / overlay buttons
CONTINUE_BTN   = pygame.Rect((SW - 280) // 2, SH // 2 + 60, 280, 58)
PLAY_AGAIN_BTN = pygame.Rect((SW - 220) // 2, SH // 2 + 60, 220, 58)

# Cell geometry
CELL_W, CELL_H = 90, 112
CELL_GAP       = 10
CELLS_PER_ROW  = 7
FARM_ORIGIN_X  = 10
FARM_ORIGIN_Y  = TOPBAR_H + 10   # = 120

# Card geometry
CARD_W, CARD_H = 118, 163
CARD_GAP       = 14
HAND_Y = TOPBAR_H + MAIN_H + 8
HAND_PANEL_X = 226
HAND_PANEL_W = 832


def kwh_to_x(kwh: float, target: float) -> int:
    frac = min(1.0, max(0.0, kwh / target))
    return int(TRACK_X0 + frac * TRACK_USABLE)


def cell_rect(idx: int) -> pygame.Rect:
    row, col = divmod(idx, CELLS_PER_ROW)
    x = FARM_ORIGIN_X + col * (CELL_W + CELL_GAP)
    y = FARM_ORIGIN_Y + row * (CELL_H + CELL_GAP)
    return pygame.Rect(x, y, CELL_W, CELL_H)


def hand_rect(idx: int, total: int) -> pygame.Rect:
    if total == 0:
        return pygame.Rect(0, HAND_Y, 0, 0)
    total_w = total * CARD_W + max(0, total - 1) * CARD_GAP
    if total_w <= HAND_PANEL_W:
        start_x = HAND_PANEL_X + (HAND_PANEL_W - total_w) // 2
        step = CARD_W + CARD_GAP
    else:
        step = max(24, (HAND_PANEL_W - CARD_W) // max(1, total - 1))
        start_x = HAND_PANEL_X
    x = start_x + idx * step
    return pygame.Rect(x, HAND_Y, CARD_W, CARD_H)


def research_card_rect(idx: int, total: int) -> pygame.Rect:
    """Rects for the 3-card research choice overlay."""
    total_w = total * 160 + max(0, total - 1) * 20
    start_x = (SW - total_w) // 2
    x = start_x + idx * (160 + 20)
    y = SH // 2 - 120
    return pygame.Rect(x, y, 160, 220)
