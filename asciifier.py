import skimage as ski
import numpy.typing as npt

LEVELS = """ .'`^",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"""
NUM_LEVELS = len(LEVELS)

def get_level_char(intensity: float):
    level_index = round(intensity * NUM_LEVELS) - 1

    return  LEVELS[level_index]

def convertGS(image: npt.NDArray, output_file='output.txt', out_dim=(256,256)):
    block_image = ski.transform.resize(image, out_dim, anti_aliasing=True)

    h, w = block_image.shape

    with open(output_file, 'w') as f:
        for i in range(h):
            line = []

            for j in range(w):
                line.append(get_level_char(block_image[i][j]))

            line.append("\n")
            f.write("".join(line))

def convertRGB(image: npt.NDArray, output_file='output.txt', out_dim=(256, 256)):
    block_image = ski.transform.resize(image, out_dim, anti_aliasing=True)
    block_image = ski.util.img_as_ubyte(block_image)

    gsBI = ski.color.rgb2gray(block_image)

    h, w, _ = block_image.shape

    with open(output_file, 'w') as f:
        for i in range(h):
            line = []

            for j in range(w):
                r,g,b = block_image[i][j]

                line.append(f"\x1b[38;2;{r};{g};{b}m{get_level_char(gsBI[i][j])}\x1b[0m")

            line.append("\n")
            f.write("".join(line))
