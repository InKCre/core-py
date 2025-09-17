from .main import ResolverManager, Resolver

__all__ = ["ResolverManager", "Resolver"]

from .image import ImageResolver
from .video import VideoResolver
from .text import TextResolver
from .webpage import WebpageResolver
