'''
Character Art

启发于最初的ASCII art，
现在将它推广到一般的等宽字符（例如：汉字）的Python代码片段。
'''
from enum import Enum
from functools import lru_cache
from itertools import zip_longest
from string import ascii_letters, digits, punctuation
from typing import Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
    from PIL.Image import fromarray
except ImportError:
    raise ImportError('需要Pillow库')

try:
    import numpy as np
    from numpy import concatenate, array, histogram, interp
except ImportError:
    raise ImportError('需要numpy库')


class Charalize:
    '''
    ## ASCII Art主体功能类

    ### 公共方法
    * *transform_C* 转换PIL Image类型为str类型
    * *transform_L* 转换PIL Image类型为PIL Image类型（L mode）
    '''

    class ResampleType(Enum):
        '''
        ### 定义重采样方式
        _从PIL里抄来的_
        '''
        NEAREST = NONE = 0
        BOX = 4
        BILINEAR = LINEAR = 2
        HAMMING = 5
        BICUBIC = CUBIC = 3
        LANCZOS = ANTIALIAS = 1

    class InterpolateWrapper:
        '''
        对一维序列进行插值

        装饰器期望被装饰函数返回一个 **一维序列**
        '''

        @staticmethod
        def nearest(fun):
            '''
            最近插值装饰器
            '''

            def execute(*args, **kwargs):
                '''
                将距离指定None元素最近的非None元素作为该指定None元素的插值
                '''
                seq = fun(*args, **kwargs)
                length = len(seq)
                fill = [None] * length
                for itor in range(length):
                    if seq[itor] is None:
                        delta = 1
                        while not fill[itor]:
                            fill[itor] = \
                                seq[itor - delta if itor - delta > 0 else 0] \
                                or \
                                seq[itor + delta if itor + delta <
                                    length - 1 else length - 1]
                            delta += 1
                return [i or j for i, j in zip(seq, fill)]

            return execute

        @staticmethod
        def dro_hooke(fun):
            '''
            胡克定律动态范围优化插值装饰器
            '''

            def execute(*args, **kwargs):
                '''
                使用类似弹簧伸缩的方法伸缩动态范围，
                基于胡克定律的等比例收缩
                '''
                seq = fun(*args, **kwargs)
                length = len(seq)
                # 从头数连续的None元素的数量
                A = next(n for n, x in enumerate(seq) if x)
                # 从末尾数连续的None元素的数量
                C = next(n for n, x in enumerate(seq[::-1]) if x)
                B = length - A - C
                if A + C == 0:
                    # 动态范围已最大，无需调整
                    return seq
                p = A * B / (A + C)
                k = (A + B + C) / B
                # x→x' : x' = ((x - (A + p)) // k) + A + p
                #           = x//k + (A + p) * (1 - 1//k)
                m = (A + p) * (1 - 1 / k)
                return [seq[int(i / k + m)] for i in range(length)]

            return execute

    def __init__(self,
                 letters= digits + ascii_letters + punctuation + ' ',
                 fontpath= 'consola.ttf',
                 fontsize= 12,
                 spacing= 0,
                 resample= ResampleType.NONE):
        self.letters = letters
        self.fontargs = (fontpath, fontsize, spacing)
        self.resample = resample
        self.mapping = self._luma2char()
        self.npmapping = self._char2pixel()

    @staticmethod
    @lru_cache(maxsize=8)
    def _getfont(fontpath: str, fontsize: int,
                 *args) -> ImageFont.FreeTypeFont:
        _ = args
        return ImageFont.truetype(fontpath, fontsize)

    @lru_cache(maxsize=8)
    def _getfontpx(self, fontpath: str, fontsize: int,
                   spacing: int) -> Tuple[int, int]:
        fontpx = (0, 0)
        for letter in self.letters:
            size = self._getfont(fontpath, fontsize).getsize(letter)
            fontpx = (max(fontpx[0], size[0]), max(fontpx[1], size[1]))
        return (fontpx[0], fontpx[1] + spacing)

    def _rendertext(self,
                    text: str,
                    imagesize: Tuple[int, int],
                    mode: str = 'L',
                    fill: int = 0,
                    ground: int = 255,
                    spacing: int = 0) -> Image.Image:
        img = Image.new(mode=mode, size=imagesize, color=ground)
        draw = ImageDraw.Draw(img)
        if '\n' in text:
            # 直接给text方法传递spacing参数居然会报错
            draw.multiline_text(
                xy=(0, 0),
                text=text,
                font=self._getfont(*self.fontargs),
                fill=fill,
                spacing=spacing)
        else:
            draw.text(
                xy=(0, 0),
                text=text,
                font=self._getfont(*self.fontargs),
                fill=fill)
        return img

    @InterpolateWrapper.nearest
    @InterpolateWrapper.dro_hooke
    def _luma2char(self) -> list:
        fontpx = self._getfontpx(*self.fontargs)
        luma2char = [None] * 256
        for letter in self.letters:
            imgl = self._rendertext(letter, fontpx)
            imgl.thumbnail((1, 1))
            luma2char[imgl.getpixel((0, 0))] = letter

        return luma2char

    def _char2pixel(self) -> np.array:
        '''
        依赖于_luma2char，注意调用次序
        '''
        pixels = []
        fontpx = self._getfontpx(*self.fontargs)
        for character in self.mapping:
            imgl = self._rendertext(character, fontpx)
            # 直接从PIL.Image到np.array可以保持数组shape
            # getdata方法会返回flatten数据，而我们并不需要flatten数据
            datal = np.array(imgl)
            pixels.append(datal)
        return np.array(pixels)

    @lru_cache(maxsize=8)
    def _scale(self, origin: Tuple[int, int]
               ) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        '''
        返回 (横纵区块数量), (调整后的尺寸)
        '''
        fontpx = self._getfontpx(*self.fontargs)
        return ((origin[0] // fontpx[0], origin[1] // fontpx[1]),
                (origin[0] - origin[0] % fontpx[0],
                 origin[1] - origin[1] % fontpx[1]))

    @staticmethod
    def _histeq(image: Image.Image, image_bins: int = 256) -> np.array:
        '''
        直方图均衡
        '''
        image_array = array(image)
        image_array2, bins = histogram(image_array, image_bins)
        cdf = image_array2.cumsum()
        cdf = (255.0 / cdf[-1]) * cdf
        return interp(image_array, bins[:-1], cdf).astype(int)

    def transform_C(self, img: Image.Image) -> str:
        '''
        ASCII Art 化的字符转换版本
        '''
        scaling, _ = self._scale(img.size)
        image = img.convert('L').resize(scaling, self.resample.value)
        # 当有且仅有一个通道的时候getdata返回的sequence的元素就是int
        # 如果有多个通道，那就是tuple，到时候lambda表达式可能要改写
        lines = [
            ''.join(map(lambda x: self.mapping[x], line))
            for line in zip_longest(*[iter(image.getdata())] * scaling[0])
        ]
        return '\n'.join(lines)

    def transform_L(self, img: Image.Image) -> Image.Image:
        '''
        ASCII Art 化的灰度转换版本
        '''
        scaling, newscale = self._scale(img.size)
        image = img.convert('L').resize(scaling, self.resample.value)
        # 到这里有用的是原图像的尺寸，原图像本身没用了
        origin_size = img.size
        imdata = self._histeq(image)
        # 现在image、scaling对象没有用了
        del img, image, scaling, newscale
        # 通过numpy直接拼合像素块，将会最大限度减少耗时
        imdata = self.npmapping[imdata]
        # 两次concatenate是这条路径的决速步，在这之前要把无用数据清理掉
        # PS 这里不用hstack，虽然函数名字更短了，但它本身还是在调用concatenate
        #    使用hstack会造成一定的性能损失
        imdata = concatenate(imdata, axis=1)
        imdata = concatenate(imdata, axis=1)
        return fromarray(imdata).resize(origin_size, self.resample.value)


if __name__ == "__main__":
    print(__doc__)