# Mosaic

A Python project for mosaic generation.

This will create a mosaic of images using an input image as a base. The mosaic
will be created by using the average color of each tile in the input image to
find the best matching image in the directory of images to use.

See [doc/architecture.md](doc/architecture.md) for a detailed description of the
project architecture, components, and data structures.

## Example - call mosaic generation with example images

```bash
make example
```

## Requirements

- Python >= 3.11
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

Prefer using `make` for development workflows. Common targets:

```bash
# Run all checks, tests, and the run target (default)
make

# Lint and format
make check

# Run unit tests
make test

# Run the application (shows help)
make run

# Run the example pipeline using test data
make example

# Clean generated files
make clean
```

If you prefer running tools directly via `uv`, the equivalents are:

```bash
uv run ruff format <files>
uv run ruff check --fix <files>
uv run pytest -v tests/test_*.py
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
| ------ | ----------- |
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
.
├── Makefile
├── pyproject.toml
├── README.md
├── LICENSE
├── doc/                  # design docs and notes
│   ├── architecture.md
│   ├── modernize-mosaic.md
│   └── performance-bottlenecks.md
├── images/               # example tile images used by `make example`
├── test_dupes/           # test data directory
├── mosaic/               # package source
│   ├── __init__.py
│   ├── __main__.py
│   └── lib.py
├── tests/                # unit tests
│   ├── test_mosaic_lib.py
│   ├── test_tile_library.py
│   ├── test_mosaic_grid.py
│   ├── test_tile_processor.py
│   ├── test_input_image.py
│   └── test_generation.py
└── README.md
```

### Coding Approach

- **Functional Programming**: The library uses functional programming
  techniques. The core logic is isolated in pure modules (`TileLibrary`,
  `MosaicGrid`) that operate on immutable data.
- **Deep Modules**: The architecture is built around deep modules that hide
  complex implementation details (like NumPy broadcasting and memory
  optimizations) behind high-leverage interfaces.
- **Tile Processing**: Image loading and processing are fused into a single
  efficient pass (`process_tile_path`), minimizing redundant pixel scans and
  improving performance.

## Documentation

The [doc](doc/) directory contains the project's design documents, performance
analyses, and other notes related to the project.

- [Architecture](doc/architecture.md)
- [Modernize Mosaic](doc/modernize-mosaic.md)
- [Performance Bottlenecks](doc/performance-bottlenecks.md)

## License

This project is licensed under the GNU General Public License v3.0 - see the
[LICENSE](LICENSE) file for details.
