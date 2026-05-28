"""
AssetManager — loads images from assets/manifest.json.
Falls back to a colored rectangle placeholder for any missing file.
To add/replace an asset: drop a PNG into assets/ and update manifest.json.
"""

import json
import os
import pygame

_BASE = os.path.join(os.path.dirname(__file__), '..', 'assets')
_MANIFEST_PATH = os.path.join(_BASE, 'manifest.json')

_surfaces: dict[str, pygame.Surface] = {}


def _placeholder(w: int, h: int, color: tuple) -> pygame.Surface:
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill(color)
    return surf


def load() -> None:
    manifest: dict = {}
    if os.path.exists(_MANIFEST_PATH):
        with open(_MANIFEST_PATH, encoding='utf-8') as f:
            manifest = json.load(f)

    defaults = {
        'background':      ((12, 18, 35),    1280, 720),
        'card_back':       ((30, 45, 80),     118, 163),
        'cell_base':       ((22, 38, 72),      90, 112),
        'track_rail':      ((40, 60, 120),   1180,   4),
        'button_normal':   ((35, 55, 95),     228,  48),
        'button_hover':    ((55, 80, 130),    228,  48),
    }

    for name, (color, w, h) in defaults.items():
        path = manifest.get(name)
        if path and os.path.exists(os.path.join(_BASE, path)):
            try:
                _surfaces[name] = pygame.image.load(os.path.join(_BASE, path)).convert_alpha()
            except Exception:
                _surfaces[name] = _placeholder(w, h, color)
        else:
            _surfaces[name] = _placeholder(w, h, color)

    # Card-specific images (loaded on demand, fall back to placeholder)
    _surfaces.setdefault('card_back', _placeholder(118, 163, (30, 45, 80)))


def get(name: str, w: int = 0, h: int = 0) -> pygame.Surface:
    surf = _surfaces.get(name)
    if surf is None:
        surf = _placeholder(max(w, 10), max(h, 10), (40, 40, 60))
        _surfaces[name] = surf
    if w and h and (surf.get_width() != w or surf.get_height() != h):
        return pygame.transform.scale(surf, (w, h))
    return surf


def get_card_image(card_id: str, w: int, h: int) -> pygame.Surface:
    if card_id not in _surfaces:
        # Try to load from manifest
        manifest: dict = {}
        if os.path.exists(_MANIFEST_PATH):
            with open(_MANIFEST_PATH, encoding='utf-8') as f:
                manifest = json.load(f)
        path = manifest.get(f'card_{card_id}')
        if path and os.path.exists(os.path.join(_BASE, path)):
            try:
                _surfaces[card_id] = pygame.image.load(os.path.join(_BASE, path)).convert_alpha()
            except Exception:
                _surfaces[card_id] = _placeholder(w, h, (30, 45, 80))
        else:
            _surfaces[card_id] = _placeholder(w, h, (30, 45, 80))
    return get(card_id, w, h)
