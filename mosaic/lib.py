import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np


def get_dominant_color(image: np.ndarray) -> Tuple[float, float, float]:
    """
    Finds the dominant color in an image.
    Uses the average color of the pixels.
    """
    # Reshape to list of pixels
    pixels = image.reshape(-1, 3)
    # Calculate average
    average_color = np.mean(pixels, axis=0)
    return tuple(average_color)


def resize_and_pad_image(image: np.ndarray, target_size: int) -> np.ndarray:
    """
    Resizes an image to fit within target_size x target_size while
    maintaining aspect ratio.
    Pads the remaining area with the dominant color to make it square.
    """
    h, w = image.shape[:2]
    scale = target_size / max(h, w)
    new_w = int(w * scale)
    new_h = int(h * scale)

    resized = cv2.resize(image, (new_w, new_h))

    # Calculate padding
    delta_w = target_size - new_w
    delta_h = target_size - new_h
    top, bottom = delta_h // 2, delta_h - (delta_h // 2)
    left, right = delta_w // 2, delta_w - (delta_w // 2)

    # Get dominant color for padding
    dominant_color = get_dominant_color(image)

    # cv2.copyMakeBorder expects a scalar color, but dominant_color
    # is a tuple/array.
    # We need to pass it correctly.
    padded_image = cv2.copyMakeBorder(
        resized,
        top,
        bottom,
        left,
        right,
        cv2.BORDER_CONSTANT,
        value=dominant_color,
    )

    return padded_image


def get_average_color(image: np.ndarray) -> np.ndarray:
    """
    Calculates the average color of an image.
    """
    return np.average(np.average(image, axis=0), axis=0)


def load_tile_metadata(
    directory: Path, target_size: int
) -> List[Dict[str, Any]]:
    """
    Loads images from a directory, processes them (resize/pad), and calculates
    average color.
    Returns a list of dictionaries with image data and average color.
    """
    tiles = []
    directory_path = Path(directory)
    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    for filepath in directory_path.iterdir():
        if not filepath.is_file():
            continue

        try:
            # Convert Path to str for cv2
            img = cv2.imread(str(filepath))

            processed_img = resize_and_pad_image(img, target_size)
            avg_color = get_average_color(processed_img)

            tiles.append(
                {
                    "filename": filepath.name,
                    "image": processed_img,
                    "average_color": avg_color,
                }
            )
        except Exception as e:
            print(f"Error processing {filepath.name}: {e}")
            continue

    return tiles  # type: ignore


def find_best_match(
    target_color: np.ndarray, tiles: List[Dict[str, Any]]
) -> np.ndarray:
    """
    Finds the tile with the closest average color to the target color.
    Uses vectorized calculation for better performance.
    """
    if not tiles:
        raise ValueError("No tiles provided to find_best_match")

    # Extract all average colors into a numpy array
    # Shape: (num_tiles, 3)
    tile_colors = np.array([tile["average_color"] for tile in tiles])

    # Calculate Euclidean distance between target_color and all tile_colors
    # target_color shape: (3,) -> broadcast to (num_tiles, 3)
    distances = np.linalg.norm(tile_colors - target_color, axis=1)

    # Find index of minimum distance
    min_index = np.argmin(distances)

    return tiles[min_index]["image"]


def calculate_grid_dimensions(
    input_h: int, input_w: int, output_size: int, tile_size: int
) -> Tuple[int, int, int, int]:
    """
    Calculates the number of tiles in X and Y directions and the actual
    output dimensions.
    """
    scale_factor = output_size / max(input_h, input_w)
    scaled_h = int(input_h * scale_factor)
    scaled_w = int(input_w * scale_factor)

    num_tiles_x = int(math.ceil(scaled_w / tile_size))
    num_tiles_y = int(math.ceil(scaled_h / tile_size))

    actual_output_w = num_tiles_x * tile_size
    actual_output_h = num_tiles_y * tile_size

    return num_tiles_x, num_tiles_y, actual_output_w, actual_output_h


def create_mosaic(
    input_image_path: Path,
    tiles_directory: Path,
    output_path: Path,
    output_size: int,
    tile_size: int,
) -> None:
    """
    Main function to create the mosaic.
    """
    # 1. Load Input Image
    input_image = cv2.imread(str(input_image_path))

    input_h, input_w = input_image.shape[:2]

    # 2. Calculate Grid
    num_tiles_x, num_tiles_y, actual_output_w, actual_output_h = (
        calculate_grid_dimensions(input_h, input_w, output_size, tile_size)
    )

    output_image = np.zeros(
        (actual_output_h, actual_output_w, 3), dtype=np.uint8
    )

    # Resize input image to match the grid structure for easier sampling
    input_small = cv2.resize(input_image, (num_tiles_x, num_tiles_y))

    # 3. Load Tiles
    tiles = load_tile_metadata(tiles_directory, tile_size)
    if not tiles:
        raise ValueError("No valid tiles found in directory.")

    # 4. Generate Mosaic
    for y in range(num_tiles_y):
        for x in range(num_tiles_x):
            # Get target color from the small input image
            target_color = input_small[y, x]

            # Find best match
            best_tile_img = find_best_match(target_color, tiles)

            # Place in output
            y_start = y * tile_size
            y_end = y_start + tile_size
            x_start = x * tile_size
            x_end = x_start + tile_size

            output_image[y_start:y_end, x_start:x_end] = best_tile_img

    # 5. Save
    cv2.imwrite(str(output_path), output_image)
