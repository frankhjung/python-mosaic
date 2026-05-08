import numpy as np

from mosaic.lib import (
    InputImage,
    MosaicGrid,
    Tile,
    TileLibrary,
    generate_mosaic,
)


def test_generate_mosaic_pure():
    """Test the entire generation pipeline in-memory (Pure Core)."""
    # 1. Setup InputImage (2x2)
    # Top-left: [10,10,10], Bottom-right: [40,40,40]
    input_arr = np.zeros((2, 2, 3), dtype=np.uint8)
    input_arr[0, 0] = [10, 10, 10]
    input_arr[1, 1] = [40, 40, 40]
    input_img = InputImage(input_arr)

    # 2. Setup MosaicGrid (tile_size 1, output_size 2)
    grid = MosaicGrid(input_h=2, input_w=2, output_size=2, tile_size=1)

    # 3. Setup TileLibrary with two tiles
    t1_img = np.zeros((1, 1, 3), dtype=np.uint8)
    t1_img[0, 0] = [0, 0, 0]
    t1 = Tile("black.jpg", t1_img, np.array([0, 0, 0], dtype=float))

    t2_img = np.zeros((1, 1, 3), dtype=np.uint8)
    t2_img[0, 0] = [255, 255, 255]
    t2 = Tile("white.jpg", t2_img, np.array([255, 255, 255], dtype=float))

    library = TileLibrary([t1, t2])

    # 4. Generate Mosaic
    # [10,10,10] is closer to Black (t1)
    # [40,40,40] is closer to Black (t1)
    # Wait, let's make it more distinct
    input_arr[1, 1] = [240, 240, 240]  # Closer to White (t2)
    input_img = InputImage(input_arr)

    mosaic = generate_mosaic(input_img, library, grid)

    assert mosaic.shape == (2, 2, 3)
    # Top-left should be t1 (black)
    assert np.array_equal(mosaic[0, 0], [0, 0, 0])
    # Bottom-right should be t2 (white)
    assert np.array_equal(mosaic[1, 1], [255, 255, 255])
