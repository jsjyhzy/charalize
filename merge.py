from abc import ABC, abstractmethod
from warnings import warn

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from char import *


class CharalizeBase(ABC):
    def __init__(self,
                 image,
                 letters=ALL,
                 font=('NotoSansCJK-Regular.ttc', 12),
                 spacing=0,
                 *args,
                 **kwargs):
        if isinstance(image, Image.Image):
            self.im = image
        else:
            self.im = Image.open(image)

        self._letters = letters
        self._spacing = spacing
        self._fontargs = font

        fontpx = (0, 0)
        for letter in self._letters:
            size = self.font.getsize(letter)
            if fontpx[0] != size[0] and fontpx != (0, 0):
                warn('Different letter width detected.')
            fontpx = (max(fontpx[0], size[0]), max(fontpx[1], size[1]))
        self._fontpx = (fontpx[0], fontpx[1] + spacing)

    @property
    def font(self):
        if getattr(self, '_font', None) is None:
            setattr(self, '_font', ImageFont.truetype(*self._fontargs))
        return getattr(self, '_font')

    @property
    def size(self):
        return self.im.size

    @property
    def fontsize(self):
        return self._fontpx

    @property
    def lettersimg(self):
        return [self.render(letter, self.fontsize) for letter in self._letters]

    @property
    def picescount(self):
        imgwidth, imgheight = self.size
        width, height = self.fontsize
        return imgwidth // width, imgheight // height

    def render(self, text, imagesize, mode='L', fill=0, ground=255, spacing=0):
        img = Image.new(mode=mode, size=imagesize, color=ground)
        draw = ImageDraw.Draw(img)
        draw.multiline_text(
            xy=(0, 0), text=text, font=self.font, fill=fill, spacing=spacing)
        return img

    def split(self, letterlist):
        return [
            ''.join(j) for j in [
                letterlist[i:i + self.picescount[0]]
                for i in range(0, len(letterlist), self.picescount[0])
            ]
        ]

    @abstractmethod
    def transform(self, *args, **kwargs):
        pass


class Blockways(CharalizeBase):
    @property
    def blocks(self):
        img = self.im.convert('L')
        width, height = self.fontsize
        wcount, hcount = self.picescount
        stacks = []
        for i in range(hcount):
            for j in range(wcount):
                stacks.append(
                    np.array(
                        img.crop((
                            j * width,
                            i * height,
                            (j + 1) * width,
                            (i + 1) * height,
                        ))).flatten())
        return np.vstack(stacks)

    @property
    def ref(self):
        return np.vstack(
            [np.array(self.lettersimg).flatten() for letter in self._letters])

    def transform(self, metric='euclidean', metric_kwargs=None):
        from sklearn import metrics
        minidx = metrics.pairwise_distances_argmin(
            self.blocks, self.ref, metric=metric, metric_kwargs=metric_kwargs)
        return '\n'.join(self.split([self._letters[i] for i in minidx]))


class Pixelways(CharalizeBase):
    @property
    def pixel(self):
        from PIL.Image import LANCZOS
        return np.array(
            self.im.convert('L').resize(
                self.picescount,
                resample=LANCZOS,
            )).flatten()

    @property
    def ref(self):
        from PIL.Image import LANCZOS
        luma = np.array([
            i.resize(
                (1, 1),
                resample=LANCZOS,
            ).getpixel((0, 0)) for i in self.lettersimg
        ])
        mapper = []
        for i in range(256):
            mapper.append(self._letters[np.argmin(np.square(luma - i))])
        return np.array(mapper)

    def transform(self):
        return '\n'.join(self.split(self.ref[self.pixel]))

