from hmf.type import *
from hmf.expr import *
from hmf.scope import Scope, Sym
from hmf.pretty import ppt
from dataclasses import dataclass


@dataclass(frozen=True)
class Env:
    types: Dict[Sym, Ty]
    scope: Scope

    @classmethod
    def top(cls):
        return Env({}, Scope.top())

    def new_scope(self):
        return Env(self.types, self.scope.sub_scope())

    def type_of_name(self, n: str):
        return self.types[self.scope.require(n)]

    def enter(self, n: str, ty: Ty):
        sym = self.scope.enter(n)
        self.types[sym] = ty


next_id = object


def error(*s):
    raise Exception(*s)


def occurs_check_adjust_level(tvar_id: object, tvar_level: int, t: Ty):
    def f(t):
        if isinstance(t, Var):
            ref = t.ref
            if isinstance(ref, Link):
                return f(ref.ty)
            if isinstance(ref, (Gen, Bound)):
                return
            if isinstance(ref, Unbound):
                if ref.id is tvar_id:
                    error("recursive types")
                elif ref.level > tvar_level:
                    t.ref = Unbound(ref.id, tvar_level)
                return
            raise TypeError(type(ref))
        if isinstance(t, App):
            f(t.f)
            f(t.arg)
            return
        if isinstance(t, Arrow):
            f(t.arg)
            f(t.ret)
            return
        if isinstance(t, Forall):
            f(t.ty)
            return
        if isinstance(t, Nom):
            return
        raise TypeError(type(t))

    f(t)


def subst_bound_vars(var_id_list: Iterable[object], ty_list: List[Ty], t: Ty):
    def f(id_ty_map: Dict[object, Ty], t):
        if isinstance(t, Nom):
            return t
        if isinstance(t, Var):
            ref = t.ref
            if isinstance(ref, Link):
                return f(id_ty_map, ref.ty)
            if isinstance(ref, Bound):
                return id_ty_map.get(ref.id) or t
            return t
        if isinstance(t, App):
            return App(f(id_ty_map, t.f), f(id_ty_map, t.arg))
        if isinstance(t, Arrow):
            return Arrow(f(id_ty_map, t.arg), f(id_ty_map, t.ret))
        if isinstance(t, Forall):
            bounds = t.bounds
            return Forall(bounds, f({k: v for k, v in id_ty_map.items() if k not in bounds}, t.ty))
        raise TypeError(type(t))

    return f(dict(zip(var_id_list, ty_list)), t)


def free_generic_vars(ty: Ty, free_var_set: set):
    def f(t):
        if isinstance(t, Nom):
            return
        if isinstance(t, Var):
            ref = t.ref
            if isinstance(ref, Link):
                return f(ref.ty)
            if isinstance(ref, (Unbound, Bound)):
                return
            if isinstance(ref, Gen):
                free_var_set.add(ty)
                return
            raise TypeError(type(ref))
        if isinstance(t, App):
            f(t.f)
            f(t.arg)
            return
        if isinstance(t, Arrow):
            f(t.arg)
            f(t.ret)
            return
        if isinstance(t, Forall):
            f(t.ty)
            return

        raise TypeError(type(ty))

    f(ty)


def escape_check(generic_var_list, ty1: Ty, ty2: Ty):
    free_var_set = set()
    free_generic_vars(ty1, free_var_set)
    free_generic_vars(ty2, free_var_set)
    return any(generic_var in free_var_set for generic_var in generic_var_list)


def unify(ty1: Ty, ty2: Ty):
    if ty1 == ty2:
        return
    if isinstance(ty1, Nom) and isinstance(ty2, Nom):
        if ty1.name == ty2.name:
            return
        error("{} mismatch {}".format(ty1, ty2))
    if isinstance(ty1, App) and isinstance(ty2, App):
        unify(ty1.f, ty2.f)
        unify(ty1.arg, ty2.arg)
        return
    if isinstance(ty1, Arrow) and isinstance(ty2, Arrow):
        unify(ty1.arg, ty2.arg)
        unify(ty1.ret, ty2.ret)
        return
    if isinstance(ty1, Var) and isinstance(ty1.ref, Link):
        unify(ty1.ref.ty, ty2)
        return
    if isinstance(ty2, Var) and isinstance(ty2.ref, Link):
        unify(ty2.ref.ty, ty1)
        return
    if isinstance(ty1, Var) and isinstance(ty2, Var):
        ref1 = ty1.ref
        ref2 = ty2.ref
        if isinstance(ref1, Unbound) and isinstance(ref2, Unbound) and ref1.id is ref2.id:
            error("more than one instance")

        if isinstance(ref1, Gen) and isinstance(ref2, Gen) and ref1.id is ref2.id:
            error("more than one instance")

        if isinstance(ref1, Bound) and isinstance(ref2, Bound):
            error("bounds should instantiate")

    if isinstance(ty2, Var) and isinstance(ty2.ref, Bound):
        error("impossible")
    if isinstance(ty1, Var) and isinstance(ty1.ref, Bound):
        error("impossible")

    if isinstance(ty2, Var) and isinstance(ty2.ref, Unbound):
        ref2 = ty2.ref
        occurs_check_adjust_level(ref2.id, ref2.level, ty1)
        ty2.ref = Link(ty1)
        return
    if isinstance(ty1, Var) and isinstance(ty1.ref, Unbound):
        ref1 = ty1.ref
        occurs_check_adjust_level(ref1.id, ref1.level, ty2)
        ty1.ref = Link(ty2)
        return
    if isinstance(ty1, Forall) and isinstance(ty2, Forall):
        # TODO: unordered
        if len(ty1.bounds) != (ty2.bounds):
            error("emm")
        n = len(ty1.bounds)
        gen_var_lst = [Var(Gen(object())) for _ in range(n)]
        gen_ty1 = subst_bound_vars(ty1.bounds, gen_var_lst, ty1.ty)
        gen_ty2 = subst_bound_vars(ty2.bounds, gen_var_lst, ty2.ty)
        unify(gen_ty1, gen_ty2)
        if not escape_check(gen_var_lst, ty1, ty2):
            return

    error("cannot unify types {} {}".format(ty1, ty2))


def subst_with_new_vars(level, var_id_lst, ty: Ty):
    var_lst = [Var(Unbound(object(), level)) for _ in var_id_lst]
    return var_id_lst, subst_bound_vars(var_id_lst, var_lst, ty)


def inst_ty_ann(level: int, var_id_lst: list, ty: Ty):
    if not var_id_lst:
        return [], ty
    return subst_with_new_vars(level, var_id_lst, ty)


def inst(level, t: Ty):
    if isinstance(t, Forall):
        _, inst_ty = subst_with_new_vars(level, t.bounds, t.ty)
        return inst_ty

    if isinstance(t, Var) and isinstance(t.ref, Link):
        return inst(level, t.ref.ty)

    return t


def subsume(level: int, t1: Ty, t2: Ty):
    inst_t2 = inst(level, t2)
    ut1 = unlink(t1)
    if isinstance(ut1, Forall):
        gen_var_lst = [Var(Gen(object())) for _ in ut1.bounds]
        gen_t1 = subst_bound_vars(ut1.bounds, gen_var_lst, ut1.ty)
        unify(gen_t1, inst_t2)
        if escape_check(gen_var_lst, ut1, t2):
            error("type {} not instance of {}".format(ut1, t2))
        return
    unify(t1, inst_t2)


def generalise(level: int, t: Ty):
    var_id_lst = []

    def f(t: Ty):
        if isinstance(t, Var):
            ref = t.ref
            if isinstance(ref, Link):
                f(ref.ty)
                return
            if isinstance(ref, Gen):
                error("impossible")
            if isinstance(ref, Bound):
                return
            if isinstance(ref, Unbound):
                if ref.level > level:
                    other_id = ref.id
                    t.ref = Bound(other_id)
                    if other_id not in var_id_lst:
                        var_id_lst.append(other_id)
                return
            raise TypeError(type(t))
        if isinstance(t, App):
            f(t.f)
            f(t.arg)
            return
        if isinstance(t, Arrow):
            f(t.arg)
            f(t.ret)
            return
        if isinstance(t, Forall):
            f(t.ty)
            return
        if isinstance(t, Nom):
            return
        raise TypeError(type(t))

    f(t)
    if not var_id_lst:
        return t
    else:
        return Forall(tuple(var_id_lst), t)


def match_fun_ty(t: Ty):
    if isinstance(t, Arrow):
        return t.arg, t.ret
    if isinstance(t, Var):
        ref = t.ref
        if isinstance(ref, Link):
            return match_fun_ty(ref.ty)
        if isinstance(ref, Unbound):
            arg = Var(Unbound(object(), ref.level))
            ret = Var(Unbound(object(), ref.level))
            t.ref = Link(Arrow(arg, ret))
            return arg, ret
    error("expected a function")


def is_annotated(e: Expr):
    if isinstance(e, EAnn):
        return True
    if isinstance(e, ELet):
        return is_annotated(e.body)
    return False


def infer(env: Env, level: int, term: Expr):
    if isinstance(term, EVar):
        try:
            return env.type_of_name(term.v)
        except KeyError:
            error("variable {} undefined".format(term.v))
    if isinstance(term, EFun):
        fn_env = env.new_scope()
        var_lst = []
        pn, ann = term.param
        if ann:
            ids, ann_ty = ann
            var_lst_sec, arg_ty = inst_ty_ann(level + 1, ids, ann_ty)
            var_lst.extend(var_lst_sec)
        else:
            arg_ty = Var(Unbound(object(), level + 1))
            var_lst.append(arg_ty)
        env.enter(pn, arg_ty)
        inferred_ret_ty = infer(fn_env, level + 1, term.body)
        if is_annotated(term.body):
            ret_ty = inferred_ret_ty
        else:
            ret_ty = inst(level + 1, inferred_ret_ty)

        if not all(map(is_mono, var_lst)):
            error("polymorphc parameter inferred: {}".format(''.join(map(ppt, var_lst))))
        return generalise(level, Arrow(arg_ty, ret_ty))

    if isinstance(term, ELet):
        var_name = term.id
        bound = term.bound
        body = term.body
        var_ty = infer(env, level + 1, bound)
        new_env = env.new_scope()
        new_env.enter(var_name, var_ty)
        return infer(new_env, level, body)

    if isinstance(term, EApp):
        fn_expr = term.f
        arg = term.arg
        fn_ty = inst(level + 1, infer(env, level + 1, fn_expr))
        param_ty, ret_ty = match_fun_ty(fn_ty)
        infer_arg(env, level + 1, param_ty, arg)
        return generalise(level, inst(level + 1, ret_ty))

    if isinstance(term, EAnn):
        _, ty = inst_ty_ann(level, *term.ann)
        expr_ty = infer(env, level, term.expr)
        subsume(level, ty, expr_ty)
        return ty
    if isinstance(term, EOmit):
        ty = Var(Unbound(object(), level))
        return ty
    if isinstance(term, EInt):
        return Nom("int")
    raise TypeError(type(term))


def infer_arg(env: Env, level, param_ty, arg_expr):
    unlink(param_ty)

    arg_ty = infer(env, level, arg_expr)
    if is_annotated(arg_expr):
        unify(param_ty, arg_ty)
    else:
        subsume(level, param_ty, arg_ty)
