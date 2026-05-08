import numpy as np
import pytest
from mosaic.lib import MosaicGrid

def test_mosaic_grid_dimensions():
    """Test that MosaicGrid correctly calculates dimensions and tile counts."""
    # Input 100x200 (H, W), output_size 400, tile_size 20
    # Scale = 400 / 200 = 2.0
    # Scaled = 200x400
    # nx = 400 / 20 = 20
    # ny = 200 / 20 = 10
    grid = MosaicGrid(input_h=100, input_w=200, output_size=400, tile_size=20)
    
    assert grid.num_tiles_x == 20
    assert grid.num_tiles_y == 10
    assert grid.output_shape == (200, 400)

def test_mosaic_grid_assemble():
    """Test that MosaicGrid correctly assembles matched tiles into a mosaic."""
    tile_size = 2
    nx, ny = 2, 2
    # 4 tiles, each 2x2x3
    # Tile 0: all 0, Tile 1: all 1, Tile 2: all 2, Tile 3: all 3
    matched_tiles = np.zeros((4, tile_size, tile_size, 3), dtype=np.uint8)
    for i in range(4):
        matched_tiles[i] = i
        
    grid = MosaicGrid(input_h=10, input_w=10, output_size=4, tile_size=tile_size)
    # Force grid layout for testing assembly directly
    grid.num_tiles_x = nx
    grid.num_tiles_y = ny
    
    mosaic = grid.assemble(matched_tiles)
    
    # Expected shape: (ny * tile_size, nx * tile_size, 3) = (4, 4, 3)
    assert mosaic.shape == (4, 4, 3)
    
    # Check layout:
    # [0 0 1 1]
    # [0 0 1 1]
    # [2 2 3 3]
    # [2 2 3 3]
    assert np.all(mosaic[0:2, 0:2] == 0)
    assert np.all(mosaic[0:2, 2:4] == 1)
    assert np.all(mosaic[2:4, 0:2] == 2)
    assert np.all(mosaic[2:4, 2:4] == 3)
