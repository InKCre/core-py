from .main import ResolverManager, Resolver

__all__ = [
    "ResolverManager",
    "Resolver",
    "ImageResolver",
    "VideoResolver",
    "TextResolver",
    "HTMLResolver",
]

from .image import ImageResolver
from .video import VideoResolver
from .text import TextResolver
from .html import HTMLResolver
