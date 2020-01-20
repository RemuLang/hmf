from hmf.infer import Env, infer
from hmf.pretty import ppt
from hmf.parser import parse
from pygments.lexers.html import RegexLexer
from pygments import token
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import prompt, PromptSession
from prompt_toolkit.lexers import PygmentsLexer
import re

keywords = ['some', 'forall', 'let', 'fun']
operators = ['->', '.']
completer = WordCompleter(keywords)


class HMFLexer(RegexLexer):
    name = 'hmf'

    tokens = {
            'root': [*[(re.escape(k), token.Keyword) for k in keywords],
                     *[(re.escape(o), token.Operator) for o in operators], (r"#([^\\#]+|\\.)*?#", token.Literal),
                     (r"\d+", token.Number),
                     (r"[-$\.a-zA-Z_\u4e00-\u9fa5][\-\!-$\.a-zA-Z0-9_\u4e00-\u9fa5]*", token.Name),
                     (r'''"([^\\"]+|\\.)*?"''', token.String), (r'\s+', token.Whitespace)]
    }


session = PromptSession(completer=completer, lexer=PygmentsLexer(HMFLexer), history=InMemoryHistory())


def repl():
    while True:
        inp: str = session.prompt('check HMF> ')
        inp = inp.strip()
        if inp.lower() == ':q':
            return
        try:
            ast = parse(inp, filename='<repl>')
            print(ppt(infer(Env.top(), 0, ast)))
        except SyntaxError as e:
            print(e)
            continue
