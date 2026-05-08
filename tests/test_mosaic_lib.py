from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

from mosaic import lib as mosaic_lib


@patch("mosaic.lib.ProcessPoolExecutor")
@patch("pathlib.Path.iterdir")
@patch("pathlib.Path.is_dir")
@patch("pathlib.Path.is_file")
@patch("cv2.imread")
def test_load_tile_metadata(
    mock_imread, mock_is_file, mock_is_dir, mock_iterdir, mock_executor
):
    mock_is_dir.return_value = True
    mock_is_file.return_value = True

    # Mock executor to run sequentially in the same process
    # to avoid pickling issues with mocks
    mock_pool = mock_executor.return_value.__enter__.return_value
    mock_pool.map.side_effect = lambda f, it: [f(x) for x in it]

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
