"""Little World's backend-independent construction API."""
from .core.blueprint import Blueprint
from .core.entity import Entity
from .core.world import World

__version__ = "0.2.0"

__all__ = ["Blueprint", "Entity", "World", "__version__"]
