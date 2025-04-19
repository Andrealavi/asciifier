import skimage as ski
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt

def get_level_char(intensity, max_value = 1):
    levels = """$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,"^`'. """
    levels = levels[::-1]

    if not type(intensity) is int:
        intensity = 0.2125*intensity[0] + 0.7154*intensity[1] + 0.0721*intensity[2]

    level_index = round((intensity * len(levels)) / max_value) - 1

    return  levels[level_index]

def convertGS(image: npt.NDArray, output_file='output.txt'):
    """
        image: is the grayscale image to convert
    """

    h, w = image.shape

    with open(output_file, 'w') as f:
        for i in range(h):
            for j in range(w):
                f.write(get_level_char(image[i][j]))
            f.write("\n")

        f.close()

def convertRGB(image: npt.NDArray, output_file='output.txt'):
    print(image.shape)
    h, w, _ = image.shape

    with open(output_file, 'w') as f:
        for i in range(h):
            for j in range(w):
                r,g,b = image[i][j]

                f.write(f"\x1b[38;2;{r};{g};{b}m{get_level_char(image[i][j], 255)}\x1b[0m")
            f.write("\n")

        f.close()

image = ski.io.imread('./tests/Redwingblackbird1.jpeg')
grayscale_image = ski.color.rgb2gray(image)

convertRGB(image)
