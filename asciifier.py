import skimage as ski
import numpy.typing as npt
import numpy as np
import concurrent.futures
import argparse

LEVELS = np.array(list(""" .'`^",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"""))
NUM_LEVELS = len(LEVELS)

def _process_row(gs_row, rgb_row):
    indices = np.round(gs_row * NUM_LEVELS).astype(int) - 1
    char_row = LEVELS[indices]

    if (rgb_row is not None):
        ascii_color = np.array(
            [f"\x1b[38;2;{r};{g};{b}m" for (r, g, b) in rgb_row]
        )

        line = np.add(ascii_color, char_row) + "\x1b[0m"
        char_row = line

    return "".join(char_row)

def convert(image, output_file, out_dim=(256,256)):
    block_image = ski.transform.resize(image, out_dim, anti_aliasing=True)

    gs_image = None
    rgb_image = None
    if (len(block_image.shape) > 2):
        gs_image = ski.color.rgb2gray(block_image)
        rgb_image = ski.util.img_as_ubyte(block_image)
    else:
        gs_image = block_image

    h = block_image.shape[0]

    lines = [None] * h

    with concurrent.futures.ProcessPoolExecutor() as executor:
        future_to_row = {executor.submit(_process_row, gs_image[i], rgb_image[i] if rgb_image is not None else None): i for i in range(h)}

        for future in concurrent.futures.as_completed(future_to_row):
            row_index = future_to_row[future]
            lines[row_index] = future.result()

    with open(output_file, 'w') as f:
        for line in lines:
            f.write(f"{line}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Asciifier",
        description="Converts images into their ASCII art representation",
    )

    parser.add_argument(
        "filename",
        type=str,
        help="Image to convert"
    )

    parser.add_argument(
        "--output",
        "-o",
        help="Output file name. Default output.txt",
        default="output.txt",
        required=False,
        type=str
    )

    parser.add_argument(
        "--grayscale",
        "-gs",
        help="The output image is in grayscale",
        type=bool,
        required=False,
        action=argparse.BooleanOptionalAction
    )

    parser.add_argument(
        "--shape",
        help="Select output file shape. Default 256x256",
        type=int,
        nargs=2,
        required=False,
        default=(256,256)
    )

    args = parser.parse_args()

    try:
        image = ski.io.imread(args.filename)

        if (args.grayscale and len(image.shape) > 2):
            image = ski.color.rgb2gray(image)

        convert(image, output_file=args.output)
    except FileNotFoundError as e:
        print(f"{args.filename} does not exist")
    except Exception as e:
        print("The following exception occured:")
        print(e)
