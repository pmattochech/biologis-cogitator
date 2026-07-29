"""Deterministic RNG helpers for optional sparks."""
from __future__ import annotations

import random
from typing import Any, Sequence, TypeVar

T = TypeVar("T")


def make_rng(seed: int | None) -> random.Random:
    return random.Random(seed if seed is not None else 0)


def weighted_choice(rng: random.Random, items: Sequence[T], weights: Sequence[float]) -> T:
    return rng.choices(list(items), weights=list(weights), k=1)[0]


def pick(rng: random.Random, items: Sequence[T]) -> T:
    return rng.choice(list(items))


def maybe_spark(spark: bool, rng: random.Random, options: Sequence[T], default: T) -> T:
    if not spark or not options:
        return default
    return pick(rng, options)
