from typing import Callable, Tuple, Union, TypedDict, Optional
from collections.abc import Iterable
import math
import functools
import random

import pygame

_NumberLike = Union[float, int]
_TupleLike = Union[Tuple[_NumberLike], _NumberLike]
_IntTupleLike = Union[Tuple[int], int]


@functools.cache
def debug_text(text: str) -> pygame.Surface:
    font = pygame.font.Font(None, 18)
    return font.render(
        text,
        True,
        (255, 0, 0),
    )


@staticmethod
def l2norm(a: Union[_NumberLike, Iterable[_NumberLike]]) -> float:
    """计算向量的L2-Norm模长"""
    if isinstance(a, (int, float)):
        return a
    elif isinstance(a, Iterable):
        return sum(i**2 for i in a) ** 0.5
    else:
        raise TypeError(f"Only accecpt tuple[number] or number.")


def dist2(rect1: pygame.Rect, rect2: pygame.Rect) -> float:
    return (rect1.centerx - rect2.centerx) ** 2 + (rect1.centery - rect2.centery) ** 2


def rint(number: float) -> int:
    """
    Examples
    ---
    - `rint(10.3)`有30%返回`11`, 70%概率返回`10`
    """
    integer = math.floor(number)
    fraction = number - integer
    return int(integer) + (random.random() < fraction)


def sign(n: int) -> int:
    if n > 0:
        return 1
    elif n < 0:
        return -1
    else:
        return 0


class IntTupleOper:
    """
    仿Numpy一维整数元组基础运算函数实现 (带有广播机制)

    Examples
    ---
    ```
    op = IntTupleOper

    op.add((1, 2), (20, 30))  # (21, 32)
    op.mul((5, 7), 4.0)  # (20, 28)
    op.div(10.0, (5, 2.0))  # (2, 5)
    ```
    """

    @staticmethod
    def oper(
        a: _TupleLike,
        b: _TupleLike,
        operator: Callable[[_NumberLike, _NumberLike], _NumberLike],
    ) -> _IntTupleLike:
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return rint(operator(a, b))

        if isinstance(b, (int, float)):  # 广播机制
            b = tuple(b for _ in a)
        elif isinstance(a, (int, float)):  # 广播机制
            a = tuple(a for _ in b)

        return tuple(rint(operator(i, j)) for i, j in zip(a, b))

    @classmethod
    def add(cls, a: _TupleLike, b: _TupleLike) -> _IntTupleLike:
        return cls.oper(a, b, lambda x, y: x + y)

    @classmethod
    def sub(cls, a: _TupleLike, b: _TupleLike) -> _IntTupleLike:
        return cls.oper(a, b, lambda x, y: x - y)

    @classmethod
    def mul(cls, a: _TupleLike, b: _TupleLike) -> _IntTupleLike:
        return cls.oper(a, b, lambda x, y: x * y)

    @classmethod
    def div(cls, a: _TupleLike, b: _TupleLike) -> _IntTupleLike:
        return cls.oper(a, b, lambda x, y: x / y)

    @classmethod
    def min(cls, a: _TupleLike, b: _TupleLike) -> _IntTupleLike:
        return cls.oper(a, b, lambda x, y: min(x, y))

    @classmethod
    def max(cls, a: _TupleLike, b: _TupleLike) -> _IntTupleLike:
        return cls.oper(a, b, lambda x, y: max(x, y))

    @classmethod
    def interp(cls, a: _TupleLike, b: _TupleLike, factor: float) -> _IntTupleLike:
        return cls.oper(a, b, lambda x, y: x * (1 - factor) + y * factor)


class RectOper:
    """
    仿Numpy的`pygame.Rect`基础运算函数实现

    同时对`size`与`topleft`进行运算。
    """

    @staticmethod
    def oper(
        a: pygame.Rect,
        b: pygame.Rect,
        operator: Callable[[_NumberLike, _NumberLike], _NumberLike],
    ) -> pygame.Rect:
        op = IntTupleOper
        size = op.oper(a.size, b.size, operator)
        topleft = op.oper(a.topleft, b.topleft, operator)
        return pygame.Rect(topleft, size)

    @classmethod
    def add(cls, a: pygame.Rect, b: pygame.Rect) -> pygame.Rect:
        return cls.oper(a, b, lambda x, y: x + y)

    @classmethod
    def sub(cls, a: pygame.Rect, b: pygame.Rect) -> pygame.Rect:
        return cls.oper(a, b, lambda x, y: x - y)

    @classmethod
    def mul(cls, a: pygame.Rect, b: pygame.Rect) -> pygame.Rect:
        return cls.oper(a, b, lambda x, y: x * y)

    @classmethod
    def div(cls, a: pygame.Rect, b: pygame.Rect) -> pygame.Rect:
        return cls.oper(a, b, lambda x, y: x / y)

    @classmethod
    def min(cls, a: pygame.Rect, b: pygame.Rect) -> pygame.Rect:
        return cls.oper(a, b, lambda x, y: min(x, y))

    @classmethod
    def max(cls, a: pygame.Rect, b: pygame.Rect) -> pygame.Rect:
        return cls.oper(a, b, lambda x, y: max(x, y))

    @classmethod
    def interp(cls, a: pygame.Rect, b: pygame.Rect, factor: float) -> pygame.Rect:
        return cls.oper(a, b, lambda x, y: x * (1 - factor) + y * factor)


def load_image_and_scale(img_path: str, rect: pygame.Rect) -> pygame.Surface:
    return pygame.transform.scale(pygame.image.load(img_path), rect.size)


class _GridInfo(TypedDict):
    cell_size: Tuple[int, int]
    grid_shape: Tuple[int, int]
    grid_range: Tuple[int, int]


def grid_info(cell_size: Tuple[int, int], grid_range: Tuple[int, int]) -> _GridInfo:
    grid_shape = tuple(math.ceil(i / j) for i, j in zip(grid_range, cell_size))
    grid_range = tuple(i * j for i, j in zip(cell_size, grid_shape))
    res: _GridInfo = {
        "cell_size": cell_size,
        "grid_range": grid_range,
        "grid_shape": grid_shape,
    }
    return res
