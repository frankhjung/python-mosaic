"""Mosaic - A tool for creating photo mosaics from collections of tile images.

This package provides both a command-line interface and a library for
generating high-performance mosaics using vectorised colour matching.
"""

from mosaic.lib import (
    MosaicGrid,
    Tile,
    TileLibrary,
    create_mosaic,
    get_average_color,
    get_dominant_color,
    load_tile_metadata,
    resize_and_pad_image,
)

__all__ = [
    "MosaicGrid",
    "Tile",
    "TileLibrary",
    "create_mosaic",
    "get_average_color",
    "get_dominant_color",
    "load_tile_metadata",
    "resize_and_pad_image",
]
