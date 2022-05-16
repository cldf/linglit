import re

from clldutils.text import replace_pattern

__all__ = ['read_tex']


def normalize_cite(t):
    def prepl(m):
        match = m.string[m.start():m.end()]
        for i, chunk in enumerate(match.split('{')):
            keys, _, _ = chunk.partition('}')
            if i:
                yield '\\cite{{{}}}'.format(keys)

    # Remove linebreaks in \cite* commands:
    t = re.sub(
        r'\\(cite[a-z]*)\n{',
        lambda m: '\\{}{{'.format(m.groups()[0]),
        t,
        flags=re.MULTILINE)

    t = replace_pattern(
        r"\\(parencites?|cites|textcites)\*?\s*(\([^)]*\)|\[[^]]*]|{[^}]+})+", prepl, t)

    t = t.replace('\\citesource{', '\\customcitesource{')

    # Replace starred commands with unstarred ones:
    t = re.sub(r'\\(cite[a-z]*)\*', lambda m: '\\{}'.format(m.groups()[0]), t)

    # Weird cases:
    t = t.replace(r'\citep[64–96],{Osborne2006}', r'\citep[64–96]{Osborne2006}')
    t = t.replace(r'\citetext{\citealp', r'{\citealp')

    # Now turn all the C|cite* variants into cite:
    t = re.sub(r'\\[Cc]ite[a-zA-Z]*\s*([\[{])', lambda m: r'\cite' + m.groups()[0], t)
    return t


def read_tex(p, with_input=True):
    """
    Read (and simplyfy) TeX from a file, resolving "input" commands.

    :param p:
    :param with_input:
    :return:
    """
    try:
        t = p.read_text(encoding='utf8')
    except UnicodeDecodeError:  # pragma: no cover
        t = p.read_text(encoding='latin1')

    t = normalize_cite(t)

    # For book 259:
    t = re.sub(
        r'\\input ([a-z]+|complex-predicates|control-raising)-include\.tex}'
        r'{\\input chapters/([a-z]+|complex-predicates|control-raising)-include\.tex}',
        lambda m: r'\input{chapters/%s-include.tex}}' % m.groups()[0],
        t
    )

    # Replace some weirdness/complexity that screws up example parsing:
    t = re.sub(r'\s*\\hfill\s*\[\\href{[^}]+}[^]]*]\s*$', '', t, re.MULTILINE)
    t = t.replace(r'\langinfobreak', r'\langinfo')  # Mostly a synonym.
    t = t.replace(r'{\db}{\db}{\db}', '[[[')
    t = t.replace(r'{\db}{\db}', '[[')
    t = t.replace(r'\textsc{id}:', '')
    t = t.replace(r'\glossN.', r'\glossN{}.')

    def repl_input(m):
        fname = m.groups()[1].strip()
        if not fname.endswith('.tex'):
            fname += '.tex'
        if not p.parent.joinpath(fname).exists() and '/' in fname:
            # look in the current directory:
            fname = fname.split('/')[-1]
        if p.parent.joinpath(fname).exists():
            yield '\n'
            yield read_tex(p.parent.joinpath(fname), with_input=False)
            yield '\n'

    if with_input:
        return replace_pattern(
            re.compile(r'^\s*\\(input|include)\s*{([^}]+)}', flags=re.MULTILINE), repl_input, t)
    return t
