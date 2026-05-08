# Mosaic Modernization Plan

## Background & Motivation

The current `mosaic` codebase correctly implements the mosaic generation logic but suffers from a significant performance bottleneck in the tile matching process, relies on imperative loops, has incomplete typing (`Any`), and lacks comprehensive documentation. The objective is to modernize the Python codebase by adopting strict Functional Programming (FP) idioms, strict type checking, comprehensive PEP 257 docstrings (in Australian English), and fully vectorized operations to maximize performance.

## Scope & Impact

- **Configuration**: Update `pyproject.toml` to enforce strict `ruff` linting rules (e.g., `UP`, `RUF`, `ANN`, `D`).
- **Core Library (`mosaic/lib.py`)**: 
  - Replace dictionaries with an immutable `Tile` dataclass.
  - Fully vectorize the distance calculation and tile matching process to eliminate `for` loops.
  - Refactor image loading to use functional constructs (`map`, `filter`, or comprehensions).
  - Add strict type annotations and Australian English documentation.
- **CLI Entry Point (`mosaic/__main__.py`)**: Improve error handling and add strict typing.
- **Tests (`tests/test_mosaic_lib.py`)**: Update existing tests to reflect the new API and data structures.

## Proposed Solution

1. **Dependency & Config Update**:

   - Update `pyproject.toml` `tool.ruff.lint.select` to include additional rules for annotations (`ANN`), pydocstyle (`D`), pyupgrade (`UP`), and ruff-specific rules (`RUF`).

2. **Architectural Simplification & Types**:

   - Introduce `@dataclass(frozen=True)` for `Tile`, containing `filename`, `image`, and `average_color`. This ensures immutability and provides better type safety than `Dict[str, Any]`.

3. **Functional & Vectorization Refactor (`mosaic/lib.py`)**:

   - `load_tile_metadata`: Remove the imperative `for` loop. Use a helper function for processing a single path and apply it over `directory_path.iterdir()` using a functional approach (e.g., comprehensions with a filter for valid files).
   - `vectorized_match_tiles`: Replace `find_best_match` and the nested `for` loops in `create_mosaic`. We will flatten the downscaled input image into an `(N, 3)` array and the tile average colors into an `(M, 3)` array. We can then compute the Redmean distance using NumPy broadcasting (or `scipy.spatial.distance` if appropriate) to find the best tile index for all `N` pixels simultaneously.
   - `create_mosaic`: Reconstruct the final image from the selected tile indices using array tiling/concatenation rather than iterative assignment.

4. **Documentation**:

   - Add Google-style docstrings (PEP 257 compliant) detailing parameters, return types, and exceptions to all functions and modules. 
   - Ensure the text uses Australian English (e.g., "colour" in descriptions), while maintaining US English for code variables (e.g., `color`).

5. **Error Handling**:

   - Replace bare `except Exception:` blocks with specific exception handling (e.g., `cv2.error`, `OSError`) or proper logging.

## Alternatives Considered

- **Moderate Refactoring**: A simpler approach would be to extract the `tile_colors` array calculation out of the inner loop but keep the `for` loops. This was rejected in favour of full vectorization to adhere to strict FP and performance goals.

## Implementation Plan

1. **Phase 1: Configuration**: Update `pyproject.toml` with strict `ruff` rules.
2. **Phase 2: Types & Data Structures**: Implement the `Tile` dataclass in `lib.py`.
3. **Phase 3: Core Logic Refactoring**: 
   - Rewrite `load_tile_metadata`.
   - Implement fully vectorized matching logic.
   - Update `create_mosaic` to use the vectorized logic.
4. **Phase 4: Documentation & CLI**: Add comprehensive docstrings to `lib.py` and `__main__.py`. Refine CLI error handling.
5. **Phase 5: Tests**: Update `test_mosaic_lib.py` to ensure complete coverage of the new vectorized implementation and `Tile` dataclass.

## Verification

- **Testing**: Execute `uv run pytest` to ensure all tests pass and coverage is maintained.
- **Linting**: Execute `uv run ruff check .` to ensure zero violations under the strict ruleset.
- **Manual Verification**: Run the CLI on sample images to verify the output matches expected quality and the execution time is improved.
- **Rebuild with Make**: Ensure the `Makefile` is updated to reflect any new dependencies or commands, and verify that `make build` and `make test` work as expected. Finally, run `make all` to ensure the entire workflow is functional.