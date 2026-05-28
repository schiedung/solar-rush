import pygame

SW, SH = 1920, 1080

TOPBAR_H = 165
MAIN_H   = 615    # SH - TOPBAR_H - HAND_H
HAND_H   = 300
FARM_W   = 1380
PANEL_W  = SW - FARM_W

# Progress track geometry
TRACK_X0 = 160
TRACK_X1 = 1635
TRACK_Y  = 118    # rail y (absolute screen y)
TRACK_USABLE = TRACK_X1 - TRACK_X0
TOKEN_R = 21

# Deck buttons (2×2 inside the painted right panel)
_DW, _DH = 225, 111
_DX0 = 1416
_DY0 = 207
_DGAP = 15
DECK_RECTS: dict[str, pygame.Rect] = {
    'material_science': pygame.Rect(_DX0,            _DY0,            _DW, _DH),
    'chemistry':        pygame.Rect(_DX0 + _DW + _DGAP, _DY0,         _DW, _DH),
    'physics':          pygame.Rect(_DX0,            _DY0 + _DH + _DGAP, _DW, _DH),
    'engineering':      pygame.Rect(_DX0 + _DW + _DGAP, _DY0 + _DH + _DGAP, _DW, _DH),
}

# Action buttons
ACTION_X   = 1416
ACTION_Y   = 477
ACTION_BTN_W = 225
ACTION_BTN_H = 66
ACTION_GAP   = 9
BUILD_BTN    = pygame.Rect(ACTION_X,                       ACTION_Y, ACTION_BTN_W, ACTION_BTN_H)
RESEARCH_BTN = pygame.Rect(ACTION_X + ACTION_BTN_W + _DGAP, ACTION_Y, ACTION_BTN_W, ACTION_BTN_H)
FINISH_TURN_BTN = pygame.Rect(ACTION_X, ACTION_Y + ACTION_BTN_H + ACTION_GAP, ACTION_BTN_W * 2 + _DGAP, ACTION_BTN_H)

# Below action buttons
STATUS_TEXT_Y    = ACTION_Y + 2 * (ACTION_BTN_H + ACTION_GAP) + 12
SCOREBOARD_Y     = STATUS_TEXT_Y + 33

# Handoff / overlay buttons
CONTINUE_BTN   = pygame.Rect((SW - 420) // 2, SH // 2 + 90, 420, 87)
PLAY_AGAIN_BTN = pygame.Rect((SW - 330) // 2, SH // 2 + 90, 330, 87)

# Cell geometry
CELL_W, CELL_H = 135, 168
CELL_GAP       = 15
CELLS_PER_ROW  = 7
FARM_ORIGIN_X  = 15
FARM_ORIGIN_Y  = TOPBAR_H + 15   # = 180

# Card geometry
CARD_W, CARD_H = 177, 245
CARD_GAP       = 21
HAND_Y = TOPBAR_H + MAIN_H + 12
HAND_PANEL_X = 339
HAND_PANEL_W = 1248


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
        step = max(36, (HAND_PANEL_W - CARD_W) // max(1, total - 1))
        start_x = HAND_PANEL_X
    x = start_x + idx * step
    return pygame.Rect(x, HAND_Y, CARD_W, CARD_H)


def research_card_rect(idx: int, total: int) -> pygame.Rect:
    """Rects for the 3-card research choice overlay."""
    total_w = total * 240 + max(0, total - 1) * 30
    start_x = (SW - total_w) // 2
    x = start_x + idx * (240 + 30)
    y = SH // 2 - 180
    return pygame.Rect(x, y, 240, 330)
