#!/usr/bin/env python
# flake8: noqa E203

"""
CLI entry point for the mosaic generation tool.

This module provides a command-line interface to create mosaic images from
a base image and a directory of tile images.
"""

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Final, NoReturn

from mosaic import lib as mosaic_lib

# Constants
ERROR_EXIT_CODE: Final[int] = 1


def get_version() -> str:
    """
    Retrieves the current version of the mosaic package.

    Returns:
        The version string or 'unknown' if the package is not installed.
    """
    try:
        return version("mosaic")
    except PackageNotFoundError:
        return "unknown"


def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments for the mosaic creation script.

    Returns:
        An argparse.Namespace object containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Create a mosaic of images using an input image as a base."
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
    )
    parser.add_argument(
        "-i",
        "--input",
        help="Path to the source image file.",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "-d",
        "--directory",
        help="Directory containing images to use as tiles.",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Path where the resulting mosaic will be saved.",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "-s",
        "--size",
        help="The desired size of the largest dimension of the mosaic.",
        required=True,
        type=int,
    )
    parser.add_argument(
        "-t",
        "--tile",
        help="The width and height of each square tile.",
        required=True,
        type=int,
    )
    return parser.parse_args()


def main() -> NoReturn:
    """
    Main execution logic for the mosaic CLI.

    Parses arguments, validates paths, and invokes the mosaic creation library.
    Exits with code 0 on success or 1 on error.
    """
    args = parse_arguments()

    # Validate input paths
    if not args.input.is_file():
        print(
            f"Error: Input image does not exist: {args.input}", file=sys.stderr
        )
        sys.exit(ERROR_EXIT_CODE)

    if not args.directory.is_dir():
        print(
            f"Error: Tiles directory does not exist: {args.directory}",
            file=sys.stderr,
        )
        sys.exit(ERROR_EXIT_CODE)

    try:
        mosaic_lib.create_mosaic(
            input_image_path=args.input,
            tiles_directory=args.directory,
            output_path=args.output,
            output_size=args.size,
            tile_size=args.tile,
        )
        print(f"Mosaic created successfully at {args.output}")
        sys.exit(0)
    except (ValueError, FileNotFoundError) as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(ERROR_EXIT_CODE)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(ERROR_EXIT_CODE)


if __name__ == "__main__":
    main()
