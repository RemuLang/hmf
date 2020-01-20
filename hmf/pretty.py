from hmf.type import *
from io import StringIO


class MissingDict(dict):

    def __init__(self, f):
        super().__init__()
        self.gen_value = f

    def __missing__(self, key):
        value = self[key] = self.gen_value(key)
        return value


def ppt(t):
    d = MissingDict(lambda _: 'a{}'.format(len(d)))
    io = StringIO()
    ppt_io(t, io, d)
    return io.getvalue()


def ppt_io(t: Ty, io: StringIO, miss: MissingDict):
    if isinstance(t, Forall):
        s1 = ' '.join(map(lambda x: miss[x], t.bounds))
        io.write('forall ')
        io.write(s1)
        io.write('. ')
        ppt_io(t.ty, io, miss)
        return
    if isinstance(t, Nom):
        io.write(t.name)
        return
    if isinstance(t, Var):
        ref = t.ref
        if isinstance(ref, Bound):
            return io.write(miss[ref.id])
        if isinstance(ref, Unbound):
            io.write('^')
            return io.write(miss[ref.id])
        if isinstance(ref, Link):
            return ppt_io(ref.ty, io, miss)
        if isinstance(ref, Gen):
            io.write('gen<')
            return io.write(miss[ref.id])
        raise
    if isinstance(t, App):
        io.write('(')
        ppt_io(t.f, io, miss)
        io.write(' ')
        ppt_io(t.arg, io, miss)
        io.write(')')
        return
    if isinstance(t, Arrow):
        io.write('(')
        ppt_io(t.arg, io, miss)
        io.write(' -> ')
        ppt_io(t.arg, io, miss)
        io.write(')')
        return
    raise TypeError(type(t))
