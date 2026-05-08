# Architecture

This document describes the architecture of the `mosaic` package: its modules,
data structures, public API, and the runtime flow of a mosaic generation run.

## Modules

| Module | Role |
| ------ | ---- |
| `mosaic/__main__.py` | CLI entry point — argument parsing, path validation, error handling |
| `mosaic/lib.py` | Core library — all image processing and mosaic assembly logic |
| `mosaic/__init__.py` | Package surface — re-exports the public API of `lib.py` |

## Data Structures

### `Tile` (frozen dataclass — `lib.py`)

Immutable record produced once per source image during tile loading. Both NumPy
arrays are marked read-only in `__post_init__` to enforce the frozen contract at
the data level.

| Field | Type | Description |
| ----- | ---- | ----------- |
| `filename` | `str` | Base name of the source file |
| `image` | `np.ndarray` `(H, W, 3)` uint8 | Resized and padded square tile, BGR |
| `average_color` | `np.ndarray` `(3,)` float64 | Mean BGR colour of the processed tile |

### NumPy array shapes used at runtime

| Name | Shape | Dtype | Where produced |
| ---- | ----- | ----- | -------------- |
| `target_colors` | `(N, 3)` | float64 | `create_mosaic` — input image downscaled to grid size then flattened; N = nx × ny |
| `tile_colors` | `(M, 3)` | float64 | `vectorized_match_tiles` — stacked from all `Tile.average_color` |
| `tile_images` | `(M, H, W, 3)` | uint8 | `vectorized_match_tiles` — stacked from all `Tile.image` |
| `distances_sq` | `(N, M)` | float64 | `vectorized_match_tiles` — Redmean² distance for every target × tile pair |
| `matched_tile_images` | `(N, H, W, 3)` | uint8 | `vectorized_match_tiles` — best tile for each grid cell |
| `grid` | `(ny, nx, H, W, 3)` | uint8 | `create_mosaic` — matched images reshaped to 2-D grid |
| `mosaic` | `(ny·H, nx·W, 3)` | uint8 | `create_mosaic` — final assembled image |

## Public API (`mosaic/__init__.py`)

```text
mosaic
├── Tile                      dataclass
├── create_mosaic()           top-level orchestrator
├── load_tile_metadata()      tile loading pipeline
├── process_single_tile()     per-file load / resize / pad
├── vectorized_match_tiles()  NumPy-vectorised colour matching
├── calculate_grid_dimensions() grid layout arithmetic
├── resize_and_pad_image()    aspect-ratio resize + dominant-colour pad
├── get_average_color()       mean BGR over all pixels
└── get_dominant_color()      RMS BGR — better perceptual representation
```

## Component Diagram

```mermaid
graph TD
    subgraph CLI ["mosaic.__main__"]
        A[parse_arguments]
        B[main]
    end

    subgraph LIB ["mosaic.lib"]
        C[create_mosaic]
        D[load_tile_metadata]
        E[process_single_tile]
        F[resize_and_pad_image]
        G[get_dominant_color]
        H[get_average_color]
        I[vectorized_match_tiles]
        J[calculate_grid_dimensions]
    end

    subgraph EXT ["External"]
        K[(Tile image files)]
        L[(Input image)]
        M[(Output mosaic)]
        N[OpenCV / cv2]
        O[NumPy]
    end

    B --> A
    B --> C

    C --> J
    C --> D
    C --> I
    C --> N

    D --> E
    E --> F
    E --> H
    E --> N

    F --> G
    F --> N

    G --> O
    H --> O
    I --> O

    K -->|"iterdir()"| D
    L --> C
    C --> M
```

## Sequence Diagram — mosaic generation

```mermaid
sequenceDiagram
    actor User
    participant CLI as __main__.main()
    participant lib as lib.create_mosaic()
    participant grid as lib.calculate_grid_dimensions()
    participant loader as lib.load_tile_metadata()
    participant tile as lib.process_single_tile()
    participant match as lib.vectorized_match_tiles()
    participant cv2 as OpenCV
    participant np as NumPy

    User->>CLI: mosaic -i img.jpg -d tiles/ -o out.jpg -s 4000 -t 50

    CLI->>CLI: parse_arguments()
    CLI->>CLI: validate paths

    CLI->>lib: create_mosaic(input, tiles_dir, output, size, tile_size)

    lib->>cv2: imread(input_image_path)
    cv2-->>lib: input_image (H×W×3)

    lib->>grid: calculate_grid_dimensions(h, w, output_size, tile_size)
    grid-->>lib: (nx, ny, out_w, out_h)

    lib->>loader: load_tile_metadata(tiles_dir, tile_size)
    loop for each image file
        loader->>tile: process_single_tile(path, tile_size)
        tile->>cv2: imread(path)
        cv2-->>tile: raw image
        tile->>cv2: resize + copyMakeBorder
        cv2-->>tile: padded square (H×W×3)
        tile->>np: average over axes → avg_color (3,)
        tile-->>loader: Tile(filename, image, avg_color)
    end
    loader-->>lib: list[Tile]  (M tiles)

    lib->>cv2: resize(input_image, (nx, ny))
    cv2-->>lib: input_small (ny×nx×3)
    lib->>np: reshape → target_colors (N×3)

    lib->>match: vectorized_match_tiles(target_colors, tiles)
    match->>np: stack tile colors → (M×3)
    match->>np: stack tile images → (M×H×W×3)
    match->>np: broadcast distances (N×1×3) vs (1×M×3) → (N×M)
    match->>np: argmin(axis=1) → best_indices (N,)
    match->>np: index tile_images[best_indices] → (N×H×W×3)
    match-->>lib: matched_tile_images (N×H×W×3)

    lib->>np: reshape → grid (ny×nx×H×W×3)
    lib->>np: swapaxes(1,2).reshape → mosaic (ny·H × nx·W × 3)

    lib->>cv2: imwrite(output_path, mosaic)
    cv2-->>lib: ok

    lib-->>CLI: (returns)
    CLI->>User: "Mosaic created successfully at out.jpg"
```

## Colour Matching — Redmean Distance

`vectorized_match_tiles` uses the **Redmean** perceptual colour distance formula
rather than plain Euclidean distance in BGR space. This gives better visual
results by weighting channels according to human colour perception:

$$
d^2 = \left(2 + \frac{\bar{r}}{256}\right)\Delta R^2
    + 4\,\Delta G^2
    + \left(2 + \frac{255 - \bar{r}}{256}\right)\Delta B^2
$$

where $\bar{r} = \frac{R_1 + R_2}{2}$.

The entire N × M distance matrix is computed in a single NumPy broadcast
operation, avoiding any Python-level loop.
