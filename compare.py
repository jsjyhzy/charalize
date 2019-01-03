from charalize import Blockways, Pixelways

FILE = 'Shirakamifubuki.jpg'

if __name__ == "__main__":
    with open('transform_luma_based.txt', 'w+') as fp:
        fp.write(Pixelways(FILE, spacing=3).transform())

    with open('transform_euclidean_distance_based.txt', 'w+') as fp:
        fp.write(Blockways(FILE, spacing=3).transform(metric='euclidean'))

    with open('transform_cosine_distance_based.txt', 'w+') as fp:
        fp.write(Blockways(FILE, spacing=3).transform(metric='cosine'))

    with open('transform_hamming_distance_based.txt', 'w+') as fp:
        fp.write(Blockways(FILE, spacing=3).transform(metric='hamming'))
