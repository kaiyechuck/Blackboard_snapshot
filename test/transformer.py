import numpy as np
from PIL import Image

class Transformer:

    _width, _height = 640, 360
    _pixel_coeffs = []

    def set_dimention(self, width, height):
        self._width = width
        self._height = height

    def set_coeffs(self, pa, pb):
        matrix = []
        for p1, p2 in zip(pa, pb):
            matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
            matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])

        A = np.matrix(matrix, dtype=np.float)
        B = np.array(pb).reshape(8)

        res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
        self._pixel_coeffs = np.array(res).reshape(8)

    def trans(self, img):
        # transform and return an PIL image
        rst = img.transform((self._width, self._height), Image.PERSPECTIVE, self._pixel_coeffs, Image.BICUBIC)#.save("1016.png")
        return rst

