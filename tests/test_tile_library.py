from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from mosaic.lib import TileLibrary


def test_tile_library_loading():
    """Test that TileLibrary correctly loads tiles from a directory."""
    with patch("mosaic.lib.load_tile_metadata") as mock_load:
        # Create a mock tile
        mock_tile = MagicMock()
        mock_tile.average_color = np.array([1, 2, 3])
        mock_tile.image = np.zeros((10, 10, 3), dtype=np.uint8)
        mock_load.return_value = [mock_tile]

        lib = TileLibrary.from_directory(Path("dummy"), 10)

        assert len(lib) == 1
        mock_load.assert_called_once_with(Path("dummy"), 10)


def test_tile_library_match():
    """Test that TileLibrary returns the best matching tile image."""
    # Setup a lib with two distinct tiles: Blue and Red
    t1_img = np.zeros((10, 10, 3), dtype=np.uint8)
    t1_img[:] = [255, 0, 0]  # BGR Blue
    t1_avg = np.array([255, 0, 0], dtype=float)

    t2_img = np.zeros((10, 10, 3), dtype=np.uint8)
    t2_img[:] = [0, 0, 255]  # BGR Red
    t2_avg = np.array([0, 0, 255], dtype=float)

    with patch("mosaic.lib.load_tile_metadata") as mock_load:
        m1 = MagicMock()
        m1.average_color = t1_avg
        m1.image = t1_img
        m2 = MagicMock()
        m2.average_color = t2_avg
        m2.image = t2_img
        mock_load.return_value = [m1, m2]

        lib = TileLibrary.from_directory(Path("dummy"), 10)

        # Match against a target that is closer to Blue
        targets = np.array([[240, 10, 10]], dtype=float)
        matches = lib.match(targets)

        assert matches.shape == (1, 10, 10, 3)
        assert np.array_equal(matches[0], t1_img)


def test_tile_library_empty_fails():
    """Test that creating a TileLibrary with no tiles raises an error."""
    with patch("mosaic.lib.load_tile_metadata") as mock_load:
        mock_load.return_value = []
        with pytest.raises(ValueError, match="No valid tiles"):
            TileLibrary.from_directory(Path("empty"), 10)
