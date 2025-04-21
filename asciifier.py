"""
Converts images into their ASCII art representation, optionally with color,
using skimage for image processing and concurrent.futures for parallelization.
"""

import skimage as ski
import numpy.typing as npt
import numpy as np
import concurrent.futures
import argparse
from typing import Tuple, Optional, List, Dict, TextIO, Any

# Array of characters representing intensity levels for ASCII art.
LEVELS = np.array(list(""" .'`^",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"""))
# The total number of intensity levels available.
NUM_LEVELS = len(LEVELS)

def _process_row(gs_row: npt.NDArray[np.float64], rgb_row: Optional[npt.NDArray[np.uint8]]) -> str:
    """
    Processes a single row of image data into an ASCII string.

    Maps grayscale intensity values to ASCII characters from LEVELS.
    If RGB data is provided, it embeds ANSI color escape codes for each character.

    Args:
        gs_row: A 1D NumPy array representing a row of grayscale pixel intensities
                (typically float values between 0.0 and 1.0).
        rgb_row: An optional 1D NumPy array of shape (width, 3) representing
                 the RGB color values (0-255) for the corresponding row.
                 If None, only grayscale ASCII art is generated.

    Returns:
        A string representing the ASCII art for the input row, potentially
        including ANSI color codes.
    """
    # Map grayscale values (0-1) to indices in the LEVELS array
    indices: npt.NDArray[np.int_] = np.round(gs_row * NUM_LEVELS).astype(int) - 1
    # Clamp indices to be within the valid range for LEVELS
    indices = np.clip(indices, 0, NUM_LEVELS - 1)
    char_row: npt.NDArray[np.str_] = LEVELS[indices]

    # If color information is available, add ANSI escape codes
    if rgb_row is not None:
        # Create ANSI color escape sequences for each pixel
        ascii_color = np.array(
            [f"\x1b[38;2;{r};{g};{b}m" for (r, g, b) in rgb_row]
        )
        # Prepend color code to each character and append reset code
        line: npt.NDArray[np.str_] = np.add(ascii_color, char_row) + "\x1b[0m"
        char_row = line # type: ignore # Numpy string addition can be tricky for type checkers

    # Join the characters/colored characters into a single string line
    return "".join(char_row)

def convert(image: npt.NDArray[Any], output_file: str, out_dim: Tuple[int, int] = (256, 256)) -> None:
    """
    Converts an input image into ASCII art and saves it to a file.

    Resizes the image, converts it to grayscale (while potentially keeping
    color information), processes each row in parallel to generate ASCII characters
    (with optional color), and writes the resulting lines to the specified output file.

    Args:
        image: The input image as a NumPy array (can be grayscale or RGB).
               Expected dtypes are typically uint8 or float.
        output_file: The path to the file where the ASCII art will be saved.
        out_dim: A tuple (height, width) specifying the desired dimensions
                 of the output ASCII art in characters. Defaults to (256, 256).
    """
    # Resize image to the target dimensions for ASCII art representation
    # Anti-aliasing helps preserve features during downscaling.
    block_image: npt.NDArray[Any] = ski.transform.resize(image, out_dim, anti_aliasing=True)

    gs_image: Optional[npt.NDArray[np.float64]] = None
    rgb_image: Optional[npt.NDArray[np.uint8]] = None

    # Check if the image has color channels
    if len(block_image.shape) > 2 and block_image.shape[2] >= 3:
        # Convert to grayscale for intensity mapping
        gs_image = ski.color.rgb2gray(block_image)
        # Keep RGB data (converted to 0-255 range) for color output
        # Ensure we handle potential alpha channels by slicing
        rgb_image = ski.util.img_as_ubyte(block_image[:, :, :3])
    else:
        # Image is already grayscale
        gs_image = block_image
        # Ensure gs_image is float if it came in as int
        if not np.issubdtype(gs_image.dtype, np.floating):
             gs_image = ski.util.img_as_float(gs_image)

    h: int = block_image.shape[0] # Height of the resized image (number of rows)

    # Pre-allocate list to store the resulting ASCII lines
    lines: List[Optional[str]] = [None] * h

    # Use a process pool to parallelize the processing of each row
    with concurrent.futures.ProcessPoolExecutor() as executor:
        # Submit each row to be processed by _process_row
        future_to_row: Dict[concurrent.futures.Future[str], int] = {
            executor.submit(_process_row, gs_image[i], rgb_image[i] if rgb_image is not None else None): i
            for i in range(h)
        }

        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_row):
            row_index: int = future_to_row[future]
            try:
                # Store the completed ASCII line in the correct position
                lines[row_index] = future.result()
            except Exception as exc:
                print(f'Row {row_index} generated an exception: {exc}')
                lines[row_index] = f"Error processing row {row_index}" # Placeholder for error

    # Write the generated ASCII lines to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in lines:
            f.write(f"{line}\n")

def main():
    # --- Command Line Argument Parsing ---
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="Asciifier",
        description="Converts images into their ASCII art representation",
    )

    parser.add_argument(
        "filename",
        type=str,
        help="Image file to convert (e.g., image.png, photo.jpg)"
    )

    parser.add_argument(
        "--output",
        "-o",
        help="Output file name for the ASCII art. Default: output.txt",
        default="output.txt",
        required=False,
        type=str
    )

    # Note: The original code used type=bool and action=BooleanOptionalAction.
    # BooleanOptionalAction is generally preferred as it creates --grayscale/--no-grayscale flags.
    # Keeping original logic here. If grayscale is True, color is disabled later.
    parser.add_argument(
        "--grayscale",
        "-gs",
        help="Force the output ASCII art to be grayscale (no color codes).",
        default=False, # Default is color if available
        required=False,
        action=argparse.BooleanOptionalAction # Creates --grayscale / --no-grayscale
    )

    parser.add_argument(
        "--shape",
        help="Output dimensions (height width) in characters. Default: 256 256",
        type=int,
        nargs=2,
        required=False,
        metavar=('HEIGHT', 'WIDTH'),
        default=(256, 256)
    )

    args: argparse.Namespace = parser.parse_args()

    # --- Image Loading and Conversion ---
    try:
        # Load the image using skimage
        image: npt.NDArray[Any] = ski.io.imread(args.filename)

        # If grayscale flag is set and image is color, convert it to grayscale *before* processing
        if args.grayscale and image.ndim > 2:
            image = ski.color.rgb2gray(image)

        # Perform the conversion
        convert(image, output_file=args.output, out_dim=args.shape)
        print(f"ASCII art saved to: {args.output}")

    except FileNotFoundError:
        print(f"Error: Input file not found at '{args.filename}'")
    except Exception as e:
        print("An unexpected error occurred:")
        print(e)

if __name__ == "__main__":
    main()
