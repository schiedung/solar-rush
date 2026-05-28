import pygame

_cache: dict = {}


def load() -> None:
    pygame.font.init()
    name = 'Segoe UI'
    _cache['tiny']   = pygame.font.SysFont(name, 17)
    _cache['small']  = pygame.font.SysFont(name, 21)
    _cache['body']   = pygame.font.SysFont(name, 24)
    _cache['bold']   = pygame.font.SysFont(name, 24, bold=True)
    _cache['medium'] = pygame.font.SysFont(name, 29)
    _cache['large']  = pygame.font.SysFont(name, 35)
    _cache['title']  = pygame.font.SysFont(name, 45, bold=True)


def get(name: str) -> pygame.font.Font:
    return _cache[name]
