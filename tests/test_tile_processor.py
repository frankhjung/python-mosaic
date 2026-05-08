import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch
from mosaic.lib import Tile, process_tile_path

def test_process_tile_path_success():
    """Test that process_tile_path fuses all processing steps into a Tile."""
    # Create a solid blue 100x50 image
    blue_img = np.zeros((50, 100, 3), dtype=np.uint8)
    blue_img[:] = [255, 0, 0]
    
    with patch("cv2.imread") as mock_imread:
        mock_imread.return_value = blue_img
        
        # Target size 10
        # Scale = 10 / 100 = 0.1
        # Resized = 5x10
        # Padded = 10x10
        tile = process_tile_path(Path("dummy.jpg"), 10)
        
        assert isinstance(tile, Tile)
        assert tile.filename == "dummy.jpg"
        assert tile.image.shape == (10, 10, 3)
        # Dominant color (blue) used for padding + blue content -> avg should be blue
        assert np.allclose(tile.average_color, [255, 0, 0])
        assert not tile.image.flags.writeable

def test_process_tile_path_invalid_image():
    """Test that process_tile_path returns None for invalid images."""
    with patch("cv2.imread") as mock_imread:
        mock_imread.return_value = None
        tile = process_tile_path(Path("bad.jpg"), 10)
        assert tile is None
