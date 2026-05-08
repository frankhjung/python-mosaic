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

### Core Modules

| Name | Role | Hides |
| ---- | ---- | ----- |
| `InputImage` | Source Logic | OpenCV I/O, resizing, flattening to target colours |
| `TileLibrary` | Memory & Matching | NumPy broadcasting, pre-stacked arrays, Redmean formula |
| `MosaicGrid` | Geometry & Assembly | Grid arithmetic, axis swapping, final reshaping |
| `TileProcessor` | Image Logic | OpenCV I/O, fused pixel scans, RMS dominant colour |

## Public API (`mosaic/__init__.py`)

```text
mosaic
├── InputImage                source image and target extraction
├── Tile                      dataclass
├── TileLibrary               matching & memory management
├── MosaicGrid                layout & assembly
├── generate_mosaic()         pure core generation pipeline
├── create_mosaic()           top-level effectful shell
├── load_tile_metadata()      tile loading pipeline
└── process_tile_path()       fused image processing pass
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
        D[generate_mosaic]
        E[InputImage]
        F[TileLibrary]
        G[MosaicGrid]
        H[load_tile_metadata]
        I[process_tile_path]
    end

    subgraph EXT ["External"]
        J[(Tile image files)]
        K[(Input image)]
        L[(Output mosaic)]
        M[OpenCV / cv2]
        N[NumPy]
    end

    B --> A
    B --> C

    C --> E
    C --> G
    C --> F
    C --> D
    C --> M

    D --> E
    D --> F
    D --> G

    F --> H
    H --> I
    I --> M
    I --> N

    E --> M
    G --> N

    J --> H
    K --> E
    D --> L
```

## Sequence Diagram — mosaic generation

```mermaid
sequenceDiagram
    actor User
    participant CLI as __main__.main()
    participant Shell as lib.create_mosaic()
    participant Core as lib.generate_mosaic()
    participant Input as lib.InputImage
    participant Grid as lib.MosaicGrid
    participant Lib as lib.TileLibrary
    participant Proc as lib.process_tile_path()
    participant cv2 as OpenCV

    User->>CLI: mosaic -i img.jpg -d tiles/ -o out.jpg -s 4000 -t 50

    CLI->>CLI: parse_arguments()
    CLI->>CLI: validate paths

    CLI->>Shell: create_mosaic(input, tiles_dir, output, size, tile_size)

    Shell->>Input: from_file(input_path)
    Input->>cv2: imread(input_path)
    Input-->>Shell: InputImage object

    Shell->>Grid: MosaicGrid(h, w, output_size, tile_size)
    Grid-->>Shell: MosaicGrid object

    Shell->>Lib: from_directory(tiles_dir, tile_size)
    Lib->>Proc: process_tile_path(path, tile_size) [Parallel]
    Proc->>cv2: imread / resize / copyMakeBorder
    Proc-->>Lib: Tile objects
    Lib-->>Shell: TileLibrary object (pre-stacked arrays)

    Shell->>Core: generate_mosaic(input_img, library, grid)

    Core->>Input: get_target_colors(grid)
    Input-->>Core: target_colors (N×3)

    Core->>Lib: match(target_colors)
    Lib-->>Core: matched_tile_images (N×H×W×3)

    Core->>Grid: assemble(matched_tile_images)
    Grid-->>Core: mosaic_array (ny·H × nx·W × 3)

    Core-->>Shell: mosaic_array

    Shell->>cv2: imwrite(output_path, mosaic_array)
    Shell-->>CLI: (returns)
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
