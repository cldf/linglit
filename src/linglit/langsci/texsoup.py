from TexSoup import TexSoup


def iter_texsoup_lines(p, level=0, tex=None):
    """
    Yield TexSoup instances for each line in a tex file, including one level of input.
    """
    tex = tex or p.read_text(encoding='utf8')
    for line in tex.splitlines():
        try:
            soup = TexSoup(line.strip(), tolerance=1)
            if soup.input:
                if level == 0:
                    pp = p.parent / '{}.tex'.format(soup.input.string)
                    if pp.exists() and pp.stat().st_size < 300:
                        yield from iter_texsoup_lines(pp, level=level + 1)
            else:
                yield soup
        except:  # pragma: no cover # noqa: E722
            pass  # pragma: no cover
