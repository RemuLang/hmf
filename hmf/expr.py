from __future__ import annotations
from dataclasses import dataclass
from typing import *
from hmf.type import Ty, Var, Bound, App, Arrow, Forall, Nom


# Expressions
@dataclass(order=True, frozen=True)
class ELet:
    id: str
    bound: Expr
    body: Expr


@dataclass(order=True, frozen=True)
class EFun:
    param: str
    body: Expr


@dataclass(order=True, frozen=True)
class EAnn:
    expr: Expr
    ann: Ty


@dataclass(order=True, frozen=True)
class EApp:
    f: Expr
    arg: Expr


@dataclass(order=True, frozen=True)
class EInt:
    v: int


@dataclass(order=True, frozen=True)
class EVar:
    v: str


@dataclass(order=True, frozen=True)
class EOmit:
    pass


Expr = Union[EOmit, EInt, EApp, EAnn, EFun, ELet]


# tagless final style bound argument for building types
def tforall(bound_names: List[str], ty_builder):
    def apply(env: Dict[str, Var]):
        ids = tuple(object() for _ in bound_names)
        env = {**env, **{n: Var(Bound(id)) for n, id in zip(bound_names, ids)}}
        return Forall(ids, ty_builder(env))

    return apply


def tapp(f_b, arg_b):
    return lambda env: App(f_b(env), arg_b(env))


def tarrow(arg_b, ret_b):
    return lambda env: Arrow(arg_b(env), ret_b(env))


def tpure(n):
    return lambda env: env.get(n, Nom(n))


def invoke(b):
    return b({})
