from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from mosaic import lib as mosaic_lib


def test_get_dominant_color():
    # Create a solid red image
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    image[:] = (0, 0, 255)  # BGR red

    color = mosaic_lib.get_dominant_color(image)
    assert color == (0.0, 0.0, 255.0)


def test_get_dominant_color_rms():
    # Create an image with two distinct colors: Black and White
    # 50 pixels black (0,0,0), 50 pixels white (255,255,255)
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    image[0:5, :] = (0, 0, 0)
    image[5:10, :] = (255, 255, 255)

    # Expected: sqrt((0^2 + 255^2)/2) = sqrt(65025/2) = sqrt(32512.5) ~= 180.31
    color = mosaic_lib.get_dominant_color(image)

    expected_val = np.sqrt((0**2 + 255**2) / 2)
    expected = (expected_val, expected_val, expected_val)

    assert np.allclose(color, expected)


@patch("cv2.resize")
def test_resize_and_pad_image(mock_resize):
    # Input image 100x50 (WxH)
    image = np.zeros((50, 100, 3), dtype=np.uint8)
    image[:] = (255, 0, 0)  # Blue

    target_size = 200

    # Mock resize to return a scaled image
    # Scale = 200 / 100 = 2.0
    # New size = 200x100
    resized_image = np.zeros((100, 200, 3), dtype=np.uint8)
    resized_image[:] = (255, 0, 0)
    mock_resize.return_value = resized_image

    result = mosaic_lib.resize_and_pad_image(image, target_size)

    # Check shape
    assert result.shape == (200, 200, 3)

    # Check center pixel
    assert np.array_equal(result[100, 100], [255, 0, 0])


def test_get_average_color():
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    image[:] = (10, 20, 30)

    avg = mosaic_lib.get_average_color(image)
    assert np.allclose(avg, [10, 20, 30])


@patch("pathlib.Path.iterdir")
@patch("pathlib.Path.is_dir")
@patch("pathlib.Path.is_file")
@patch("cv2.imread")
def test_load_tile_metadata(
    mock_imread, mock_is_file, mock_is_dir, mock_iterdir
):
    mock_is_dir.return_value = True
    mock_is_file.return_value = True

    # Mock iterdir to return Path objects
    file1 = MagicMock(spec=Path)
    file1.name = "img1.jpg"
    file1.is_file.return_value = True
    file1.__str__.return_value = "dummy_dir/img1.jpg"

    file2 = MagicMock(spec=Path)
    file2.name = "img2.jpg"
    file2.is_file.return_value = True
    file2.__str__.return_value = "dummy_dir/img2.jpg"

    mock_iterdir.return_value = [file1, file2]

    # Create dummy images
    img1 = np.zeros((10, 10, 3), dtype=np.uint8)
    img1[:] = (0, 0, 0)
    img2 = np.zeros((10, 10, 3), dtype=np.uint8)
    img2[:] = (255, 255, 255)

    mock_imread.side_effect = [img1, img2]

    tiles = mosaic_lib.load_tile_metadata(Path("dummy_dir"), 20)

    assert len(tiles) == 2
    assert isinstance(tiles[0], mosaic_lib.Tile)
    assert tiles[0].filename == "img1.jpg"
    assert np.allclose(tiles[0].average_color, [0, 0, 0])
    assert tiles[1].filename == "img2.jpg"
    assert np.allclose(tiles[1].average_color, [255, 255, 255])


def test_calculate_grid_dimensions():
    # Case 1: Perfect fit
    nx, ny, w, h = mosaic_lib.calculate_grid_dimensions(100, 200, 400, 20)
    assert nx == 20
    assert ny == 10
    assert w == 400
    assert h == 200

    # Case 2: Rounding up
    nx, ny, w, h = mosaic_lib.calculate_grid_dimensions(100, 100, 105, 10)
    assert nx == 11
    assert ny == 11
    assert w == 110
    assert h == 110
