#!/usr/bin/env python
# flake8: noqa E203


"""
Create a mosaic of images using an input image as a base.
"""

import argparse
import sys
from importlib.metadata import version
from pathlib import Path

import mosaic


def main():
    """
    Main entry point for the mosaic creation script.

    Parses command line arguments and calls the mosaic creation library.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Create a mosaic of images using an input image as a base."
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {version('mosaic')}",
    )
    parser.add_argument(
        "-i", "--input", help="Input image", required=True, type=Path
    )
    parser.add_argument(
        "-d",
        "--directory",
        help="Directory of images to use",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "-o", "--output", help="Output image", required=True, type=Path
    )
    parser.add_argument(
        "-s", "--size", help="Size of output image", required=True, type=int
    )
    parser.add_argument(
        "-t", "--tile", help="Tile size", required=True, type=int
    )
    args = parser.parse_args()

    # Check that the input image exists
    if not args.input.is_file():
        print("Input image does not exist")
        sys.exit(1)
    # Check that the directory exists
    if not args.directory.is_dir():
        print("Directory does not exist")
        sys.exit(1)

    try:
        mosaic.create_mosaic(
            input_image_path=args.input,
            tiles_directory=args.directory,
            output_path=args.output,
            output_size=args.size,
            tile_size=args.tile,
        )
        print(f"Mosaic created successfully at {args.output}")
    except Exception as e:
        print(f"Error creating mosaic: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
