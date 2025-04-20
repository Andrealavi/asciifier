import skimage as ski
import numpy as np
import numpy.typing as npt

def quantizeGrayscale(image):
    scaling_factor = 1/256

    return np.clip(image / scaling_factor, a_min=0, a_max=255)

def is_rgb(image):
    return len(image.shape) > 2

def get_level_char(intensity, max_value = 255):
    levels = """$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,"^`'. """
    levels = levels[::-1]

    if len(intensity) == 1:
        intensity = intensity[0]
    else:
        intensity = 0.2125 * intensity[0] + 0.7154 * intensity[1] + 0.0721 * intensity[2]

    level_index = round((intensity * len(levels)) / max_value) - 1

    return  levels[level_index]

def subsample_image(image):
    if len(image.shape) == 2:
        image = quantizeGrayscale(image)
        image = np.reshape(image, shape=(image.shape[0], image.shape[1], 1))

    h, w, c = image.shape

    if h % 2 != 0:
        h += 1
        image = np.vstack((image, np.zeros((1, w, c))))

    if w % 2 != 0:
        w += 1
        image = np.hstack((image, np.zeros((h, 1, c))))

    sub_img = np.zeros((h//2, w//2, c), dtype=np.float32)

    blk_i = 0
    for i in range(0, h, 2):
        blk_j = 0
        for j in range(0, w, 2):
            for k in range(c):
                block = image[i:i+2, j:j+2, k]

                blk_mean = np.round(np.mean(block))

                sub_img[blk_i][blk_j][k] = blk_mean

            blk_j += 1

        blk_i += 1

    return sub_img

def convertGS(image: npt.NDArray, output_file='output.txt'):
    block_image = subsample_image(image)
    h, w, _ = block_image.shape

    with open(output_file, 'w') as f:
        for i in range(h):
            for j in range(w):
                f.write(get_level_char(block_image[i][j]))
            f.write("\n")

        f.close()

def convertRGB(image: npt.NDArray, output_file='output.txt'):
    block_image = subsample_image(image)
    #block_image = image
    h, w, _ = block_image.shape

    with open(output_file, 'w') as f:
        for i in range(h):
            for j in range(w):
                r,g,b = block_image[i][j].astype(np.uint8)

                f.write(f"\x1b[38;2;{r};{g};{b}m{get_level_char(block_image[i][j])}\x1b[0m")
            f.write("\n")

        f.close()
