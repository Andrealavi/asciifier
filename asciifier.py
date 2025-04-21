import skimage as ski
import numpy.typing as npt
import numpy as np
import concurrent.futures

LEVELS = np.array(list(""" .'`^",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"""))
NUM_LEVELS = len(LEVELS)

def _process_row_gs(img_row):
    indices = np.round(img_row * NUM_LEVELS).astype(int) - 1
    char_row = LEVELS[indices]

    return "".join(char_row)

def _process_row_rgb(img_row, rgb_row):
    indices = np.round(img_row * NUM_LEVELS).astype(int) - 1
    char_row = LEVELS[indices]

    line = []
    for char, (r, g, b) in zip(char_row, rgb_row):
        line.append(f"\x1b[38;2;{r};{g};{b}m{char}\x1b[0m")

    return "".join(line)

def convertGS(image: npt.NDArray, output_file='output.txt', out_dim=(256,256)):
    block_image = ski.transform.resize(image, out_dim, anti_aliasing=True)
    h, w = block_image.shape

    lines = [None] * h
    with concurrent.futures.ProcessPoolExecutor() as executor:
        future_to_row = {executor.submit(_process_row_gs, block_image[i]): i for i in range(h)}

        for future in concurrent.futures.as_completed(future_to_row):
            row_index = future_to_row[future]
            lines[row_index] = future.result()

    with open(output_file, 'w', encoding="utf-8") as f:
        for line in lines:
            f.write(f"{line}\n")

def convertRGB(image: npt.NDArray, output_file='output.txt', out_dim=(256, 256)):
    block_image = ski.transform.resize(image, out_dim, anti_aliasing=True)
    block_image = ski.util.img_as_ubyte(block_image)

    gsBI = ski.color.rgb2gray(block_image)

    h, w, _ = block_image.shape

    lines = [None] * h
    with concurrent.futures.ProcessPoolExecutor() as executor:
        future_to_row = {executor.submit(_process_row_rgb, gsBI[i], block_image[i]): i for i in range(h)}

        for future in concurrent.futures.as_completed(future_to_row):
            row_index = future_to_row[future]
            lines[row_index] = future.result()

    with open(output_file, 'w') as f:
        for line in lines:
            f.write(f"{line}\n")
