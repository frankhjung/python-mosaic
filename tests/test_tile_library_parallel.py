from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

from mosaic.lib import Tile, TileLibrary


def test_tile_library_uses_parallel_loading():
    """Test that TileLibrary utilizes ProcessPoolExecutor for loading."""
    # We must patch where it is IMPORTED, which is mosaic.lib
    with patch("mosaic.lib.ProcessPoolExecutor") as mock_executor:
        # Setup mock executor
        mock_instance = mock_executor.return_value.__enter__.return_value

        # Mock tiles to return
        t1 = Tile(
            "t1.jpg", np.zeros((10, 10, 3), dtype=np.uint8), np.array([0, 0, 0])
        )
        t2 = Tile(
            "t2.jpg", np.zeros((10, 10, 3), dtype=np.uint8), np.array([1, 1, 1])
        )
        mock_instance.map.return_value = [t1, t2]

        # Mock Path.is_dir and Path.iterdir in mosaic.lib
        with (
            patch("mosaic.lib.Path.is_dir", return_value=True),
            patch("mosaic.lib.Path.iterdir") as mock_iterdir,
        ):
            p1 = MagicMock(spec=Path)
            p1.is_file.return_value = True
            p2 = MagicMock(spec=Path)
            p2.is_file.return_value = True

            mock_iterdir.return_value = [p1, p2]

            lib = TileLibrary.from_directory(Path("dummy"), 10)

        assert len(lib) == 2
        # Verify map was called
        assert mock_instance.map.called
        args, _ = mock_instance.map.call_args
        # Check that the first argument is our partial function
        assert args[0].func.__name__ == "process_tile_path"
        assert list(args[1]) == [p1, p2]
