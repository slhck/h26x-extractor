import importlib.metadata

from .h26x_parser import H26xParser

__version__ = importlib.metadata.version("h26x_extractor")

__all__ = ["H26xParser"]
