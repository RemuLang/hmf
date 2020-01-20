from enum import Enum
from hmf.infer import *

del infer
del infer_arg


class GenKind(Enum):
    Generalised = 0
    Instantiated = 1


def should_gen(expected_ty: Ty):
    if isinstance(expected_ty, Forall):
        return GenKind.Generalised
    if isinstance(expected_ty, Var) and isinstance(expected_ty.ref, Link):
        return should_gen(expected_ty.ref.ty)
    return GenKind.Instantiated


def maybe_gen(generalised: GenKind, level: int, ty: Ty):
    if generalised == GenKind.Instantiated:
        return ty
    return generalise(level, ty)


def maybe_inst(generalised: GenKind, level: int, ty: Ty):
    if generalised == GenKind.Instantiated:
        return inst(level, ty)
    return ty


def gen_or_inst(generalised: GenKind, level: int, ty: Ty):
    if generalised == GenKind.Instantiated:
        return inst(level, ty)
    return generalise(level, ty)


def infer(env: Env, level: int, maybe_expected_ty, generalised, term: Expr):
    if isinstance(term, EVar):
        try:
            return maybe_inst(generalised, level, env.type_of_name(term.v))
        except KeyError:
            error("variable {} undefined".format(term.v))
    if isinstance(term, EFun):
        if not maybe_expected_ty:
            param = term.param
            expected_ret_ty = None
            body_generalised = GenKind.Instantiated
        else:
            inst_ed = inst(level + 1, maybe_expected_ty)
            if isinstance(inst_ed, Arrow):
                param_name, ann = term.param
                expect_param_ty = inst_ed.arg
                expected_ret_ty = inst_ed.ret
                param = param_name, ([], expect_param_ty) if not maybe_expected_ty else ann
                body_generalised = should_gen(expected_ret_ty)
            else:
                param = term.param
                expected_ret_ty = None
                body_generalised = GenKind.Instantiated

        fn_env = env.new_scope()
        var_lst = []
        pn, ann = param
        if ann:
            var_lst_sec, arg_ty = inst_ty_ann(level + 1, *ann)
            var_lst.extend(var_lst_sec)
        else:
            arg_ty = Var(Unbound(object(), level + 1))
            var_lst.append(arg_ty)
        fn_env.enter(pn, arg_ty)
        ret_ty = infer(fn_env, level + 1, expected_ret_ty, body_generalised, term.body)

        if not all(map(is_mono, var_lst)):
            error("polymorphc parameter inferred: {}".format(''.join(map(ppt, var_lst))))

        ret_ty = maybe_gen(generalised, level, Arrow(arg_ty, ret_ty))
        return ret_ty

    if isinstance(term, ELet):
        var_name = term.id
        bound = term.bound
        body = term.body
        var_ty = infer(env, level + 1, None, GenKind.Generalised, bound)
        new_env = env.new_scope()
        new_env.enter(var_name, var_ty)
        return infer(new_env, level, maybe_expected_ty, generalised, body)

    if isinstance(term, EApp):
        fn_expr = term.f
        arg = term.arg
        fn_ty = inst(level + 1, infer(env, level + 1, None, GenKind.Instantiated, fn_expr))
        param_ty, ret_ty = match_fun_ty(fn_ty)
        inst_ed_ret_ty = inst(level + 1, ret_ty)
        if not maybe_expected_ty or isinstance(inst_ed_ret_ty, Var) and isinstance(inst_ed_ret_ty.ref, Unbound):
            pass
        elif maybe_expected_ty:
            unify(inst(level + 1, maybe_expected_ty), inst_ed_ret_ty)
        else:
            error("dont know what to do")
        infer_arg(env, level + 1, param_ty, arg)
        return gen_or_inst(generalised, level, inst_ed_ret_ty)

    if isinstance(term, EAnn):
        _, ty = inst_ty_ann(level, *term.ann)
        expr_ty = infer(env, level, ty, should_gen(ty), term.expr)
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
    arg_ty = infer(env, level, param_ty, should_gen(param_ty), arg_expr)
    if is_annotated(arg_expr):
        unify(param_ty, arg_ty)
    else:
        subsume(level, param_ty, arg_ty)


def infer_top(env, level, term):
    return infer(env, level, None, GenKind.Generalised, term)
