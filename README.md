# Mosaic

A Python project for mosaic generation.

This will create a mosaic of images using an input image as a base. The mosaic
will be created by using the average color of each tile in the input image to
find the best matching image in the directory of images to use.

## Example - call mosaic generation with example images

```bash
make example
```

## Requirements

- Python >= 3.10
- [uv](https://github.com/astral-sh/uv) package manager

### Dependencies

- `numpy` - Numerical computing
- `opencv-python-headless` - Image processing

## Quick Start

This project uses [uv](https://github.com/astral-sh/uv) for package management.

### Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Initialize Environment

Sync the environment and install dependencies:

```bash
uv sync
```

### Run Checks and Tests

You can run the standard checks using `make` (which uses `uv` internally) or run
them directly with `uv`:

```bash
# Using Make
make

# Using uv directly
uv run ruff check .
uv run pytest
```

### Fix Ruff Warnings with uv

Use Ruff's auto-fix mode to resolve fixable lint warnings:

```bash
# Check and automatically fix warnings where possible
uv run ruff check --fix .

# (Optional) Apply formatting as well
uv run ruff format .
```

**Tip:** `make check` already runs formatting and `ruff check --fix` for this
project.

### Run the Application

```bash
# Using Make
make run

# Using uv directly
uv run mosaic -h
```

## CLI Usage

```bash
mosaic -i INPUT -d DIRECTORY -o OUTPUT -s SIZE -t TILE
```

| Option | Description |
|--------|-------------|
| `-i, --input` | Path to the input image |
| `-d, --directory` | Directory containing tile images |
| `-o, --output` | Path for the output mosaic image |
| `-s, --size` | Size of the output image (in pixels) |
| `-t, --tile` | Size of each tile (in pixels) |

### CLI Example

```bash
uv run mosaic -i photo.jpg -d tiles/ -o mosaic.jpg -s 2000 -t 50
```

## API Usage

You can also use the library programmatically:

```python
from pathlib import Path
import mosaic

mosaic.create_mosaic(
    input_image_path=Path("photo.jpg"),
    tiles_directory=Path("tiles/"),
    output_path=Path("mosaic.jpg"),
    output_size=2000,
    tile_size=50,
)
```

## Development

- **Linting**: `make check`
- **Testing**: `make test`
- **Clean**: `make clean`

## Implementation Details

The project follows a standard Python package structure:

### Project Structure

```text
mosaic/
├── mosaic/
│   ├── __init__.py      # Package init, exports public API
│   ├── __main__.py      # CLI entry point for `python -m mosaic`
│   └── lib.py           # Core library functions
├── tests/
│   └── test_mosaic_lib.py
├── pyproject.toml
├── Makefile
└── README.md
```

### Coding Approach

- **Functional Programming**: The library uses functional programming
  techniques. Functions are pure where possible and avoid maintaining global
  state.
- **Library Separation**: Core logic is isolated in `mosaic/lib.py`, making it
  easy to test and reuse.
- **Tile Processing**: The `resize_and_pad_image` function handles non-square
  images by scaling them to fit the target tile size while maintaining aspect
  ratio, and padding the rest with the image's dominant color.

## License

This project is licensed under the GNU General Public License v3.0 - see the
[LICENSE](LICENSE) file for details.
