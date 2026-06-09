from typing import Generic, Iterable, Iterator, Optional, TypeVar
from collections.abc import Sequence
from itertools import combinations

from multiset import FrozenMultiset, Multiset


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
        seq[i + shift_by] if i + shift_by < len(seq) else typ() for i in range(len(seq))
    ]

def left_shift_in_place(seq: list[T], shift_by: int = 1) -> None:
    if len(seq) == 0:
        return
    typ = type(seq[0])
    for i in range(len(seq)):
        if i + shift_by < len(seq):
            seq[i] = seq[i + shift_by]
        else:
            seq[i] = typ()


def right_shift(seq: Sequence[T], shift_by: int = 1) -> list[T]:
    if len(seq) == 0:
        return []
    typ = type(seq[0])
    return [typ() if i < shift_by else seq[i - shift_by] for i in range(len(seq))]


def find_indices(seq: Sequence[T], elem_to_find: T) -> list[int]:
    return [i for i, elem in enumerate(seq) if elem == elem_to_find]

def combinations_min_max(
    iterable: Iterable[T],
    min_size: int,
    max_size: int,
) -> Iterator[T]:
    for k in range(min_size, max_size + 1):
        yield from combinations(iterable, k)

"""
def combinations_from_multiset(
    multiset: Multiset[T], subset_size: int
) -> Iterator[FrozenMultiset[T]]:
    elements = multiset.keys()
    count = multiset.values()
    current_count = []
    for i in count:
        """



def combinations_from_multiset_min_max(
    multiset: Multiset[T], min_subset_size: int, max_subset_size: int
) -> Iterator[FrozenMultiset[T]]:
    for k in range(min_subset_size, max_subset_size + 1):
        yield from combinations_from_multiset(multiset, k)