from typing import TypeVar, Iterator
from collections.abc import Sequence

T = TypeVar("T")


def stringify(iter: Iterator[T]) -> str:
    return "".join(str(elem) for elem in iter)


def cyclic_left_shift(list_: list[T], shift_by: int) -> list[T]:
    return [list_[(i + shift_by) % len(list_)] for i in range(len(list_))]


def left_shift(list_: list[T], shift_by: int) -> list[T]:
    return [
        list_[(i + shift_by) if i + shift_by < len(list_) else 0]
        for i in range(len(list_))
    ]


def find_indices(seq: Sequence[T], elem_to_find: T) -> list[int]:
    return [i for i, elem in enumerate(seq) if elem == elem_to_find]
