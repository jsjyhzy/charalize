from string import ascii_letters, digits, punctuation

import numpy
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from sklearn import metrics

from char import ALL


def vec(im):
    return numpy.array(im).flatten()


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


class Preprocess:
    def __init__(self, path, picesize):
        self.im = Image.open(path)
        self.picesize = picesize

    @property
    def size(self):
        return self.im.size

    @property
    def picecount(self):
        imgwidth, imgheight = self.size
        width, height = self.picesize
        return imgwidth // width, imgheight // height

    def enhance_edge(self, ratio=0.5):
        self.im = Image.blend(self.im,
                              self.im.filter(ImageFilter.EDGE_ENHANCE), ratio)

    def enhance_blur(self, radius=2):
        self.im = self.im.filter(ImageFilter.GaussianBlur(radius=radius))

    def crop(self):
        width, height = self.picesize
        wcount, hcount = self.picecount
        for i in range(hcount):
            for j in range(wcount):
                part = self.im.crop((
                    j * width,
                    i * height,
                    (j + 1) * width,
                    (i + 1) * height,
                ))
                part = part.convert('L')
                yield part

    def vectors(self):
        return numpy.vstack([vec(i) for i in self.crop()])


class Charalize:
    def __init__(self,
                 letters=ALL,
                 fontpath='NotoSansCJK-Regular.ttc',
                 fontsize=12,
                 spacing=0):
        self.letters = letters
        self.spacing = spacing
        self._fontargs = (fontpath, fontsize)
        fontpx = (0, 0)
        for letter in self.letters:
            size = self.font.getsize(letter)
            fontpx = (max(fontpx[0], size[0]), max(fontpx[1], size[1]))
        self.fontpx = (fontpx[0], fontpx[1] + spacing)
        self.ref = numpy.vstack([
            vec(
                self._render(
                    letter, self.fontpx, ground=255, mode='L', fill=0))
            for letter in self.letters
        ])

    @property
    def font(self):
        if getattr(self, '_font', None) is None:
            setattr(self, '_font', ImageFont.truetype(*self._fontargs))
        return getattr(self, '_font')

    def _render(self, text, imagesize, mode, fill, ground, spacing=0):
        img = Image.new(mode=mode, size=imagesize, color=ground)
        draw = ImageDraw.Draw(img)
        draw.multiline_text(
            xy=(0, 0), text=text, font=self.font, fill=fill, spacing=spacing)
        return img

    def transform(self, imagepath, metric='euclidean'):
        pro = Preprocess(imagepath, self.fontpx)
        pro.enhance_edge()
        vecs = pro.vectors()
        ans = metrics.pairwise_distances_argmin(vecs, self.ref, metric=metric)
        wcnt, _ = pro.picecount

        return '\n'.join(
            [''.join(i) for i in chunks([self.letters[i] for i in ans], wcnt)])
