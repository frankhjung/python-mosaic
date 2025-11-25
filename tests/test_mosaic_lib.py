from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

from mosaic import lib as mosaic_lib


def test_get_dominant_color():
    # Create a solid red image
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    image[:] = (0, 0, 255)  # BGR red

    color = mosaic_lib.get_dominant_color(image)
    assert color == (0.0, 0.0, 255.0)


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

    # Check padding color (should be dominant color of input, which is blue)
    # The center should be the image, top/bottom should be padded
    # Top padding: 0 to 50
    # Image: 50 to 150
    # Bottom padding: 150 to 200

    # Check center pixel
    assert np.array_equal(result[100, 100], [255, 0, 0])

    # Check padding pixel (top left)
    # Dominant color is (255, 0, 0)
    assert np.array_equal(result[10, 10], [255, 0, 0])


def test_get_average_color():
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    image[:] = (10, 20, 30)

    avg = mosaic_lib.get_average_color(image)
    assert np.allclose(avg, [10, 20, 30])


@patch("pathlib.Path.iterdir")
@patch("pathlib.Path.exists")
@patch("pathlib.Path.is_file")
@patch("cv2.imread")
def test_load_tile_metadata(
    mock_imread, mock_is_file, mock_exists, mock_iterdir
):
    mock_exists.return_value = True

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

    tiles = mosaic_lib.load_tile_metadata("dummy_dir", 20)

    assert len(tiles) == 2
    assert tiles[0]["filename"] == "img1.jpg"
    assert np.allclose(tiles[0]["average_color"], [0, 0, 0])
    assert tiles[1]["filename"] == "img2.jpg"
    assert np.allclose(tiles[1]["average_color"], [255, 255, 255])


def test_find_best_match():
    tiles = [
        {"image": "img1", "average_color": np.array([0, 0, 0])},
        {"image": "img2", "average_color": np.array([100, 100, 100])},
        {"image": "img3", "average_color": np.array([255, 255, 255])},
    ]

    target = np.array([10, 10, 10])
    match = mosaic_lib.find_best_match(target, tiles)
    assert match == "img1"

    target = np.array([200, 200, 200])
    match = mosaic_lib.find_best_match(target, tiles)
    assert match == "img3"


def test_calculate_grid_dimensions():
    # Case 1: Perfect fit
    # Input: 100x200 (HxW), Output size: 400, Tile size: 20
    # Scale = 2.0 -> Scaled: 200x400
    # Tiles X = 400/20 = 20
    # Tiles Y = 200/20 = 10
    nx, ny, w, h = mosaic_lib.calculate_grid_dimensions(100, 200, 400, 20)
    assert nx == 20
    assert ny == 10
    assert w == 400
    assert h == 200

    # Case 2: Rounding up
    # Input: 100x100, Output size: 105, Tile size: 10
    # Scale = 1.05 -> Scaled: 105x105
    # Tiles X = ceil(105/10) = 11
    # Tiles Y = ceil(105/10) = 11
    # Actual W = 110
    # Actual H = 110
    nx, ny, w, h = mosaic_lib.calculate_grid_dimensions(100, 100, 105, 10)
    assert nx == 11
    assert ny == 11
    assert w == 110
    assert h == 110
