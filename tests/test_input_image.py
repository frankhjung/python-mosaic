from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from mosaic.lib import InputImage, MosaicGrid


def test_input_image_from_file_success():
    """Test successful loading of an InputImage."""
    dummy_img = np.zeros((100, 200, 3), dtype=np.uint8)
    with patch("cv2.imread") as mock_imread:
        mock_imread.return_value = dummy_img

        img = InputImage.from_file(Path("dummy.jpg"))

        assert img.height == 100
        assert img.width == 200


def test_input_image_from_file_fails():
    """Test loading a non-existent or invalid image."""
    with patch("cv2.imread") as mock_imread:
        mock_imread.return_value = None

        with pytest.raises(ValueError, match="Could not load input image"):
            InputImage.from_file(Path("missing.jpg"))


def test_input_image_get_target_colors():
    """Test that it resizes to the grid and extracts target colors."""
    # Create an image that is 4x4
    # Top left: 0, Top right: 1
    # Bottom left: 2, Bottom right: 3
    dummy_img = np.zeros((4, 4, 3), dtype=np.uint8)

    with patch("cv2.imread", return_value=dummy_img):
        img = InputImage.from_file(Path("dummy.jpg"))

        # Grid requiring 2x2 layout
        grid = MosaicGrid(input_h=4, input_w=4, output_size=2, tile_size=1)
        assert grid.num_tiles_x == 2
        assert grid.num_tiles_y == 2

        with patch("cv2.resize") as mock_resize:
            # Mock the resized 2x2 image
            resized = np.zeros((2, 2, 3), dtype=np.uint8)
            resized[0, 0] = [10, 10, 10]
            resized[0, 1] = [20, 20, 20]
            resized[1, 0] = [30, 30, 30]
            resized[1, 1] = [40, 40, 40]
            mock_resize.return_value = resized

            targets = img.get_target_colors(grid)

            mock_resize.assert_called_once()
            # It should have resized to (nx, ny) -> (2, 2)
            assert mock_resize.call_args[0][1] == (2, 2)

            # Should be shape (4, 3)
            assert targets.shape == (4, 3)
            assert np.array_equal(targets[0], [10, 10, 10])
            assert np.array_equal(targets[3], [40, 40, 40])
