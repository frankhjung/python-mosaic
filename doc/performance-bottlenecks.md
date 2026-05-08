# Performance Bottlenecks

Analysis of `mosaic/lib.py` (May 2026).

## 1. Single-threaded tile loading — `load_tile_metadata` (High impact)

Each tile is loaded from disk, decoded by OpenCV, resized, padded, and
colour-averaged **sequentially**. For large tile libraries (1 000+ images) this
dominates total runtime.

**Fix:** parallelise with `concurrent.futures.ThreadPoolExecutor` (I/O-bound
decode) or `ProcessPoolExecutor` (CPU-bound resize/pad):

```python
from concurrent.futures import ThreadPoolExecutor

def load_tile_metadata(directory: Path, target_size: int) -> list[Tile]:
    paths = [p for p in directory.iterdir() if p.is_file()]
    with ThreadPoolExecutor() as executor:
        results = executor.map(
            lambda p: process_single_tile(p, target_size), paths
        )
    return [t for t in results if t is not None]
```

## 2. Full tile-image stack allocated in `vectorized_match_tiles` (High impact)

```python
tile_images = np.array([t.image for t in tiles])  # (M, H, W, 3)
```

This copies **all** tile pixel data into one contiguous array on every call. For
M = 5 000 tiles at 50 × 50 px this is ≈ 1.8 GB of RAM and a large allocation
cost.

**Fix:** Pre-stack tile images and colours once at load time, storing them as
module-level arrays rather than per-`Tile` fields. Only the colour stack (tiny:
M × 3 floats) is needed for matching; the image stack is only indexed after
`argmin`:

```python
# Build once after load_tile_metadata
tile_colors = np.array([t.average_color for t in tiles])  # (M, 3)
tile_images = np.stack([t.image for t in tiles])           # (M, H, W, 3)

# Pass pre-built arrays into vectorized_match_tiles instead of list[Tile]
```

This eliminates repeated re-stacking and allows the image array to live in
shared memory if multiprocessing is adopted (bottleneck 1).

## 3. Redundant full-image scan in `process_single_tile` (Medium impact)

Both `get_dominant_color` (called inside `resize_and_pad_image`) and
`get_average_color` (called after) iterate over all pixels of the image
independently:

```python
processed_img = resize_and_pad_image(img, target_size)  # scans pixels
avg_color = get_average_color(processed_img)             # scans pixels again
```

**Fix:** Fuse into a single pass, or compute `dominant_color` from the resized
image (since it is used only for padding) and return it alongside the image to
avoid re-scanning:

```python
def resize_and_pad_image(
    image: np.ndarray, target_size: int
) -> tuple[np.ndarray, np.ndarray]:
    ...
    dominant_color = get_dominant_color(image)
    padded = cv2.copyMakeBorder(...)
    avg_color = np.average(padded, axis=(0, 1))
    return padded, avg_color
```

Eliminates one full pixel scan per tile.

## Summary

| # | Location | Impact | Fix |
| - | -------- | ------ | --- |
| 1 | `load_tile_metadata` | High — scales with tile count | Thread/process pool |
| 2 | `vectorized_match_tiles` | High — memory & allocation | Pre-stack arrays at load time |
| 3 | `process_single_tile` | Medium — 2× pixel scans per tile | Fuse colour computation |
