from __future__ import annotations
from dataclasses import dataclass
from typing import *


class Ty:
    pass


@dataclass(order=True, frozen=True)
class Nom(Ty):
    name: str


@dataclass(order=True, frozen=True)
class App(Ty):
    f: Ty
    arg: Ty


@dataclass(order=True, frozen=True)
class Arrow(Ty):
    arg: Ty
    ret: Ty


@dataclass(order=True, frozen=True)
class Forall(Ty):
    bounds: Tuple[object, ...]
    ty: Ty


@dataclass
class Var(Ty):
    ref: TVar

    def __init__(self, ref: TVar):
        self.ref = ref


@dataclass(order=True, frozen=True)
class Unbound:
    id: object
    level: int


@dataclass(order=True, frozen=True)
class Link:
    ty: Ty


@dataclass(order=True, frozen=True)
class Gen:
    id: object


@dataclass(order=True, frozen=True)
class Bound:
    id: object


TVar = Union[Unbound, Gen, Link, Bound]


def unlink(t: Ty):
    if isinstance(t, Var) and isinstance(t.ref, Link):
        ty = unlink(t.ref.ty)
        t.ref = ty
        return ty
    return t


def is_mono(t: Ty):
    if isinstance(t, Forall):
        return False
    if isinstance(t, Nom):
        return True
    if isinstance(t, Var) and isinstance(t.ref, Link):
        return is_mono(t.ref.ty)
    if isinstance(t, Var):
        return True
    if isinstance(t, App):
        return is_mono(t.f) and is_mono(t.arg)
    if isinstance(t, Arrow):
        return is_mono(t.arg) and is_mono(t.ret)
    raise TypeError(type(t))
