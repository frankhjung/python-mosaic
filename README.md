# Mosaic

A Python project for mosaic generation.

This will create a mosaic of images using an input image as a base. The mosaic will be created by using the average color of each tile in the input image to find the best matching image in the directory of images to use.

## Example

```bash
make example
```

## Quick Start

This project uses [uv](https://github.com/astral-sh/uv) for package management.

### Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Run checks and tests

```bash
make
```

This will automatically install dependencies and run linting and tests.

### Run the application

```bash
make run
```

## Development

- **Linting**: `make check`
- **Testing**: `make test`
- **Clean**: `make clean`

## Implementation Details

The project is structured into a CLI tool (`mosaic.py`) and a reusable library (`mosaic_lib.py`).

### Coding Approach

- **Functional Programming**: The library uses functional programming techniques. Functions are pure where possible and avoid maintaining global state.
- **Library Separation**: Core logic is isolated in `mosaic_lib.py`, making it easy to test and reuse.
- **Tile Processing**: The `resize_and_pad_image` function handles non-square images by scaling them to fit the target tile size while maintaining aspect ratio, and padding the rest with the image's dominant color.
