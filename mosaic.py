#!/usr/bin/env python
# flake8: noqa E203


"""
Create a mosaic of images using an input image as a base.
"""


#
# MAIN
#
# Parse command line arguments:
#  -i <input image>
#  -d <directory of images to use>
#  -o <output image>
#  -s <size of output image>
#  -t <tile size>

import argparse
import math
import os
import sys

import numpy as np
import cv2


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Create a mosaic of images using an input image as a base."
    )
    parser.add_argument("-i", "--input", help="Input image", required=True)
    parser.add_argument(
        "-d", "--directory", help="Directory of images to use", required=True
    )
    parser.add_argument("-o", "--output", help="Output image", required=True)
    parser.add_argument(
        "-s", "--size", help="Size of output image", required=True
    )
    parser.add_argument("-t", "--tile", help="Tile size", required=True)
    args = parser.parse_args()
    # Check that the input image exists
    if not os.path.isfile(args.input):
        print("Input image does not exist")
        sys.exit(1)
    # Check that the directory exists
    if not os.path.isdir(args.directory):
        print("Directory does not exist")
        sys.exit(1)

    # Read the input image
    input_image = cv2.imread(args.input)
    # Get the size of the input image
    input_height, input_width, input_channels = input_image.shape
    # Get the size of the output image
    output_size = int(args.size)
    # Get the tile size
    tile_size: int = int(args.tile)
    # Get the number of tiles in the x and y directions
    num_tiles_x = int(math.ceil(float(input_width) / tile_size))
    num_tiles_y = int(math.ceil(float(input_height) / tile_size))
    # Create the output image
    output_image = np.zeros(
        (output_size, output_size, input_channels), np.uint8
    )
    # Get the size of each tile in the output image
    output_tile_size_x = int(math.ceil(float(output_size) / num_tiles_x))
    output_tile_size_y = int(math.ceil(float(output_size) / num_tiles_y))
    # Get the list of images in the directory
    image_list: list[str] = os.listdir(args.directory)
    # Loop over the tiles
    for tile_y in range(num_tiles_y):
        for tile_x in range(num_tiles_x):
            # Get the tile from the input image
            tile = input_image[
                tile_y * tile_size : (tile_y + 1) * tile_size,
                tile_x * tile_size : (tile_x + 1) * tile_size,
            ]
            # Get the average color of the tile
            average_color_per_row: float = np.average(tile, axis=0)
            average_color = np.average(average_color_per_row, axis=0)
            # Get the best match for the tile
            best_match = get_best_match(
                image_list, average_color, args.directory
            )
            # Read the best match
            best_match_image = cv2.imread(
                os.path.join(args.directory, best_match)
            )
            # Resize the best match to the output tile size
            best_match_image = cv2.resize(
                best_match_image, (output_tile_size_x, output_tile_size_y)
            )
            # Copy the best match into the output image
            output_image[
                tile_y * output_tile_size_y : (tile_y + 1) * output_tile_size_y,
                tile_x * output_tile_size_x : (tile_x + 1) * output_tile_size_x,
            ] = best_match_image
    # Write the output image
    cv2.imwrite(args.output, output_image)


def get_best_match(image_list, average_color, directory):
    # Set the initial minimum distance to a large value
    min_distance = 1000000
    # Loop over the images
    for image in image_list:
        # Read the image
        image_bgr = cv2.imread(os.path.join(directory, image))
        # Get the average color of the image
        average_color_per_row: float = np.average(image_bgr, axis=0)
        average_color_image = np.average(average_color_per_row, axis=0)
        # Compute the Euclidean distance between the colors
        distance = math.sqrt(
            math.pow(average_color[0] - average_color_image[0], 2)
            + math.pow(average_color[1] - average_color_image[1], 2)
            + math.pow(average_color[2] - average_color_image[2], 2)
        )
        # Check if this is the best match so far
        if distance < min_distance:
            min_distance = distance
            best_match = image
    # Return the best match
    return best_match
