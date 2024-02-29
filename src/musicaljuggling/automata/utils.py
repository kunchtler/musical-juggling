from typing import TypeVar
from collections.abc import Sequence


T = TypeVar("T")


def stringify(seq: Sequence[T]) -> str:
    return "".join(str(elem) for elem in seq)


def cyclic_left_shift(seq: Sequence[T], shift_by: int = 1) -> list[T]:
    return [seq[(i + shift_by) % len(seq)] for i in range(len(seq))]


def cyclic_right_shift(seq: Sequence[T], shift_by: int = 1) -> list[T]:
    return [seq[(i - shift_by) % len(seq)] for i in range(len(seq))]


def left_shift(seq: Sequence[T], shift_by: int = 1) -> list[T]:
    if len(seq) == 0:
        return []
    typ = type(seq[0])
    return [
        seq[(i + shift_by)] if i + shift_by < len(seq) else typ()
        for i in range(len(seq))
    ]


def right_shift(seq: Sequence[T], shift_by: int = 1) -> list[T]:
    if len(seq) == 0:
        return []
    typ = type(seq[0])
    return [typ() if i < shift_by else seq[i - shift_by] for i in range(len(seq))]


def find_indices(seq: Sequence[T], elem_to_find: T) -> list[int]:
    return [i for i, elem in enumerate(seq) if elem == elem_to_find]
