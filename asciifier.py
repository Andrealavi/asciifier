import skimage as ski
import numpy.typing as npt
import numpy as np
import concurrent.futures

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

def convert(image, output_file='output.txt', out_dim=(256,256)):
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
