# Glossary

Domain language for the Mosaic project.

## Terms

**Input Image** — The source image that defines the composition of the final
Mosaic.

**Tile** — A small, processed image used as a building block for the Mosaic.
Each Tile has a pre-calculated average color for matching.

**Tile Library** — A collection of available Tiles. Provides matching
capabilities to find the best Tile for a given Target Color.

**Target Color** — A BGR color value representing a cell in the downsampled
Input Image that needs to be matched to a Tile.

**Redmean Distance** — A perceptual color distance formula used to find the
best match between a Target Color and a Tile's average color.

**Mosaic** — The final assembled image composed of many Tiles.

**Grid** — The logical 2D layout of Tiles in the Mosaic, defined by the Input
Image dimensions and the Tile size.
