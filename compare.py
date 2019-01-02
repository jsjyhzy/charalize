from PIL import Image

from charalize import ALL, FILE


def legency():
    from legency import Charalize
    with open('tarnsform_luma_based.txt', 'w+') as fp:
        fp.write(Charalize(spacing=5).transform_C(Image.open(FILE)))


def newone():
    from charalize import Charalize
    with open('tarnsform_euclidean_distance_based.txt', 'w+') as fp:
        fp.write(Charalize(spacing=3).transform(FILE, metric='euclidean'))

def wtf():
    from charalize import Charalize
    with open('tarnsform_hamming_distance_based.txt', 'w+') as fp:
        fp.write(Charalize(spacing=3).transform(FILE, metric='hamming'))

legency()
newone()
wtf()