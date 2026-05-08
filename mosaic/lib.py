"""Library for creating mosaics from collections of images.

This module provides functions for image analysis, tile processing, and
vectorised mosaic construction using NumPy and OpenCV.
"""

import math
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Final, cast

import cv2  # type: ignore
import numpy as np

# Constants
BITS_PER_CHANNEL: Final[int] = 256
MAX_COLOUR_VALUE: Final[int] = 255


@dataclass(frozen=True)
class Tile:
    """Metadata for a mosaic tile image.

    Attributes:
        filename: The name of the source image file.
        image: The processed (resized and padded) image data.
        average_color: The average BGR colour of the image as a NumPy array.

    """

    filename: str
    image: np.ndarray
    average_color: np.ndarray

    def __post_init__(self) -> None:
        """Mark stored arrays as read-only to honour frozen semantics."""
        self.image.flags.writeable = False
        self.average_color.flags.writeable = False


def process_tile_path(filepath: Path, target_size: int) -> Tile | None:
    """Load and process a single image file into a Tile.

    Fuses loading, dominant color calculation, resizing, padding, and
    average color calculation into a single pass to minimize pixel scans.

    Args:
        filepath: Path to the image file.
        target_size: Desired square size for the tile.

    Returns:
        A Tile object if successful, otherwise None.

    """
    try:
        img = cast(np.ndarray | None, cv2.imread(str(filepath)))
        if img is None:
            return None

        # 1. Calculate dominant color using RMS before resizing
        rms = np.sqrt(
            np.mean(np.square(img.reshape(-1, 3).astype(float)), axis=0)
        )
        dominant_color = (float(rms[0]), float(rms[1]), float(rms[2]))

        # 2. Resize maintaining aspect ratio
        h, w = img.shape[:2]
        scale = target_size / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        resized = cast(np.ndarray, cv2.resize(img, (new_w, new_h)))

        # 3. Pad to square with dominant color
        delta_w = target_size - new_w
        delta_h = target_size - new_h
        top, bottom = delta_h // 2, delta_h - (delta_h // 2)
        left, right = delta_w // 2, delta_w - (delta_w // 2)

        processed_img = cv2.copyMakeBorder(
            resized,
            top,
            bottom,
            left,
            right,
            cv2.BORDER_CONSTANT,
            value=dominant_color,
        )

        # 4. Calculate average color of the final processed tile
        avg_color = np.average(processed_img, axis=(0, 1))

        return Tile(
            filename=filepath.name,
            image=processed_img,
            average_color=avg_color,
        )
    except (OSError, cv2.error) as e:  # type: ignore[misc]
        print(f"Error processing {filepath.name}: {e}")
        return None


def load_tile_metadata(directory: Path, target_size: int) -> list[Tile]:
    """Load and process all images from a directory into Tiles in parallel.

    Args:
        directory: The directory containing source images.
        target_size: The size to which each tile should be processed.

    Returns:
        A list of processed Tile objects.

    Raises:
        FileNotFoundError: If the directory does not exist.

    """
    if not directory.is_dir():
        raise FileNotFoundError(f"Directory not found: {directory}")

    paths = [p for p in directory.iterdir() if p.is_file()]
    if not paths:
        return []

    # Use process pool for CPU-bound image processing
    process_func = partial(process_tile_path, target_size=target_size)
    with ProcessPoolExecutor() as executor:
        results = list(executor.map(process_func, paths))

    return [t for t in results if t is not None]


class TileLibrary:
    """A collection of tiles with optimized matching capabilities."""

    def __init__(self, tiles: list[Tile]) -> None:
        """Initialize the library with a list of tiles.

        Args:
            tiles: A list of Tile objects.

        Raises:
            ValueError: If the tiles list is empty.

        """
        if not tiles:
            raise ValueError("No valid tiles provided for matching.")

        self._tiles = tiles
        # Pre-stack tile data into contiguous arrays for performance
        self._tile_colors = np.array([t.average_color for t in tiles])
        self._tile_images = np.array([t.image for t in tiles])

    @classmethod
    def from_directory(cls, directory: Path, tile_size: int) -> "TileLibrary":
        """Load tiles from a directory and create a TileLibrary.

        Args:
            directory: Path to the directory containing tile images.
            tile_size: The square size each tile should be processed into.

        Returns:
            A new TileLibrary instance.

        """
        tiles = load_tile_metadata(directory, tile_size)
        return cls(tiles)

    def match(self, target_colors: np.ndarray) -> np.ndarray:
        """Match multiple target colours to the best available tiles.

        Uses NumPy broadcasting to calculate the Redmean distance between every
        target colour and every tile average colour simultaneously.

        Args:
            target_colors: A NumPy array of shape (N, 3) representing
                BGR targets.

        Returns:
            A NumPy array of shape (N, tile_h, tile_w, 3) containing the best
            matching tile images.

        """
        # Prepare for broadcasting: (N, 1, 3) vs (1, M, 3)
        t_colors = target_colors[:, np.newaxis, :]
        s_colors = self._tile_colors[np.newaxis, :, :]

        # Extract B, G, R components for Redmean distance formula
        r_t, r_s = t_colors[..., 2], s_colors[..., 2]
        rmean = (r_t + r_s) / 2.0

        dr = r_t - r_s
        dg = t_colors[..., 1] - s_colors[..., 1]
        db = t_colors[..., 0] - s_colors[..., 0]

        # Calculate squared Redmean distances (N, M)
        w_r = 2.0 + rmean / BITS_PER_CHANNEL
        w_g = 4.0
        w_b = 2.0 + (MAX_COLOUR_VALUE - rmean) / BITS_PER_CHANNEL

        distances_sq = (w_r * dr**2) + (w_g * dg**2) + (w_b * db**2)

        # Find the index of the best matching tile for each target pixel
        best_indices = np.argmin(distances_sq, axis=1)

        return self._tile_images[best_indices]

    def __len__(self) -> int:
        """Return the number of tiles in the library."""
        return len(self._tiles)


class MosaicGrid:
    """Handles the geometric layout and assembly of a mosaic."""

    def __init__(
        self, input_h: int, input_w: int, output_size: int, tile_size: int
    ) -> None:
        """Calculate grid layout and dimensions.

        Args:
            input_h: Original image height.
            input_w: Original image width.
            output_size: Target size for the largest dimension.
            tile_size: The square size of each tile.

        """
        self.tile_size = tile_size
        scale_factor = output_size / max(input_h, input_w)
        scaled_h, scaled_w = (
            int(input_h * scale_factor),
            int(input_w * scale_factor),
        )

        self.num_tiles_x = math.ceil(scaled_w / tile_size)
        self.num_tiles_y = math.ceil(scaled_h / tile_size)
        self.actual_w = self.num_tiles_x * tile_size
        self.actual_h = self.num_tiles_y * tile_size

    @property
    def output_shape(self) -> tuple[int, int]:
        """Return the final (H, W) of the mosaic."""
        return (self.actual_h, self.actual_w)

    def assemble(self, matched_tiles: np.ndarray) -> np.ndarray:
        """Assemble a flat array of matched tile images into a mosaic grid.

        Args:
            matched_tiles: Array of shape (N, th, tw, 3).

        Returns:
            The final assembled mosaic image.

        """
        # Reshape matched tiles back into a grid: (ny, nx, th, tw, 3)
        grid = matched_tiles.reshape(
            self.num_tiles_y,
            self.num_tiles_x,
            self.tile_size,
            self.tile_size,
            3,
        )

        # Assemble by rearranging axes and collapsing the grid
        # (ny, nx, th, tw, 3) -> (ny, th, nx, tw, 3) -> (ny*th, nx*tw, 3)
        return grid.swapaxes(1, 2).reshape(self.actual_h, self.actual_w, 3)


class InputImage:
    """Represents the source image that defines the mosaic composition."""

    def __init__(self, image: np.ndarray) -> None:
        """Initialize with an image array.

        Args:
            image: The loaded BGR image.

        """
        self._image = image
        self.height, self.width = image.shape[:2]

    @classmethod
    def from_file(cls, filepath: Path) -> "InputImage":
        """Load an InputImage from a file path.

        Args:
            filepath: Path to the image file.

        Returns:
            A new InputImage instance.

        Raises:
            ValueError: If the image cannot be loaded.

        """
        img = cast(np.ndarray | None, cv2.imread(str(filepath)))
        if img is None:
            raise ValueError(f"Could not load input image: {filepath}")
        return cls(img)

    def get_target_colors(self, grid: MosaicGrid) -> np.ndarray:
        """Extract the target colours for the mosaic grid.

        Resizes the input image to match the grid dimensions and flattens it
        into a 1D array of colours.

        Args:
            grid: The MosaicGrid defining the layout.

        Returns:
            A NumPy array of shape (N, 3) where N is the number of tiles.

        """
        resized = cast(
            np.ndarray,
            cv2.resize(self._image, (grid.num_tiles_x, grid.num_tiles_y)),
        )
        return resized.reshape(-1, 3)


def create_mosaic(
    input_image_path: Path,
    tiles_directory: Path,
    output_path: Path,
    output_size: int,
    tile_size: int,
) -> None:
    """Generate a mosaic and save it to a file.

    Args:
        input_image_path: Path to the source image.
        tiles_directory: Directory containing images to use as tiles.
        output_path: Path where the resulting mosaic will be saved.
        output_size: The desired size of the mosaic.
        tile_size: The size of each square tile.

    Raises:
        ValueError: If no valid tiles are found or input image is invalid.

    """
    input_img = InputImage.from_file(input_image_path)
    grid = MosaicGrid(input_img.height, input_img.width, output_size, tile_size)

    # Load and process tiles into an optimized library
    library = TileLibrary.from_directory(tiles_directory, tile_size)

    # Extract target colours for matching
    target_colors = input_img.get_target_colors(grid)

    # Match all tiles at once using the library's optimized interface
    matched_tile_images = library.match(target_colors)

    # Assemble the final image using the grid's pure logic
    mosaic = grid.assemble(matched_tile_images)

    cv2.imwrite(str(output_path), mosaic)
