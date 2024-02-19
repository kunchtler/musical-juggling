from typing import TypeVar, Iterator
from collections.abc import Sequence

T = TypeVar("T")


def stringify(iter: Iterator[T]) -> str:
    return "".join(str(elem) for elem in iter)


def cyclic_left_shift(list_: list[T], shift_by: int = 1) -> list[T]:
    return [list_[(i + shift_by) % len(list_)] for i in range(len(list_))]


def cyclic_right_shift(list_: list[T], shift_by: int = 1) -> list[T]:
    return [list_[(i - shift_by) % len(list_)] for i in range(len(list_))]


def left_shift(list_: list[T], shift_by: int = 1) -> list[T]:
    if len(list_) == 0:
        return []
    typ = type(list_[0])
    return [
        list_[(i + shift_by)] if i + shift_by < len(list_) else typ()
        for i in range(len(list_))
    ]


def right_shift(list_: list[T], shift_by: int = 1) -> list[T]:
    if len(list_) == 0:
        return []
    typ = type(list_[0])
    return [typ() if i < shift_by else list_[i - shift_by] for i in range(len(list_))]


def find_indices(seq: Sequence[T], elem_to_find: T) -> list[int]:
    return [i for i, elem in enumerate(seq) if elem == elem_to_find]
