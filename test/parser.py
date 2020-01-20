from hmf.parser import parse

assert str(parse("""
let x = 1 in x
""")) == "ELet(id='x', bound=EInt(v=1), body=EVar(v='x'))"

assert (str(parse("""
let x = 1 in (x: int)
""")) == "ELet(id='x', bound=EInt(v=1), body=EAnn(expr=EVar(v='x'), ann=([], Nom(name='int'))))")

assert str(parse("fun (x: tuple int int) -> snd x")) == """
EFun(param=('x', ([], App(f=App(f=Nom(name='tuple'), arg=Nom(name='int')), arg=Nom(name='int')))), body=EApp(f=EVar(v='snd'), arg=EVar(v='x')))
""".strip()

assert str(parse("func a b c d : int")) == """
EAnn(expr=EApp(f=EApp(f=EApp(f=EApp(f=EVar(v='func'), arg=EVar(v='a')), arg=EVar(v='b')), arg=EVar(v='c')), arg=EVar(v='d')), ann=([], Nom(name='int')))
""".strip()

print(parse("fun (a: some a. a -> b) -> a"))
print(parse("fun (a: forall a. a -> b) -> a"))
