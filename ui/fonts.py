import pygame

_cache: dict = {}


def load() -> None:
    pygame.font.init()
    name = 'Segoe UI'
    _cache['tiny']   = pygame.font.SysFont(name, 11)
    _cache['small']  = pygame.font.SysFont(name, 14)
    _cache['body']   = pygame.font.SysFont(name, 16)
    _cache['bold']   = pygame.font.SysFont(name, 16, bold=True)
    _cache['medium'] = pygame.font.SysFont(name, 19)
    _cache['large']  = pygame.font.SysFont(name, 23)
    _cache['title']  = pygame.font.SysFont(name, 30, bold=True)


def get(name: str) -> pygame.font.Font:
    return _cache[name]
