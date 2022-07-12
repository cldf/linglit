import functools
import re
import typing
import hashlib

from pyigt.igt import IGT, NON_OVERT_ELEMENT
from pyigt.lgrmorphemes import MORPHEME_SEPARATORS
from TexSoup import TexSoup
from TexSoup.data import TexCmd

from linglit.base import Example, Publication
from .latex import to_text, strip_tex_comment

__all__ = ['iter_gll', 'make_example']

STARTINGQUOTE = "`‘"
ENDINGQUOTE = "'’"
EMPTY = NON_OVERT_ELEMENT
ELLIPSIS = '…'
CHAR_REPLS = {
    r'\v{s}': 'š',
    r"\'u": 'ú',
    r'\v{h}': "ȟ",
    r"\'a": "á",
}


def parse_langinfo(line):
    def get_name(arg):
        if len(arg.contents) == 1 and \
                isinstance(arg.contents[0], TexCmd) and \
                not arg.contents[0].args:
            return '\\' + arg.contents[0].name
        return ''.join(TexSoup(re.sub(r'\\label{[^}]+}', '', arg.string)).text)

    langinfo = TexSoup(r'\langinfo' + line.split(r'\langinfo')[-1], tolerance=1).langinfo
    if langinfo and len(langinfo.args) == 3:
        return (
            get_name(langinfo.args[0]),
            ''.join(TexSoup(langinfo.args[1].string).text),
            '_'.join(TexSoup(langinfo.args[2].string).text or ['']),
        )


def parse_cmd(cmd, line):
    try:
        # Cut out the command and its first argument from line:
        texcmd = '\\' + cmd + '{' + line.split('\\' + cmd + '{')[-1].split('}')[0]
        cmd = getattr(TexSoup(texcmd, tolerance=1), cmd)
    except:  # noqa: E722
        raise ValueError(line)  # pragma: no cover
    return (cmd.args[0].string.split('!')[-1], '', '')


parse_ili = functools.partial(parse_cmd, 'ili')
parse_il = functools.partial(parse_cmd, 'il')


def iter_gll(s):
    """
    Loop over the lines in a TeX file, detecting examples by matching start- and end-lines.

    FIXME: 123:
    \\syacex{Noun}{Pronoun}{984}
    {ܗܲܝܡܵܢܘܼܬ݂ܹܗ}
    {haymānut-ēh}
    {faith-\\poss.3\\masc}
    {his faith}
    {\\cite[70, \\S 91e]{MuraokaSyriac}}
    """
    gll_start = re.compile(r'\\(g[l]{2,3}|exg\.|ag\.|bg\.)([^a-zA-Z]|$)')
    glt_start = re.compile(r'\\(glt|trans|Transl|TranslMulti|rede)([^a-zA-Z]|$)')
    longexampleandlanguage_pattern = re.compile(r'\\\\}{([^}]+)}$')

    linfo = None
    ex_pattern = re.compile(
        r"\\ex\s+(?P<lname>[A-Z][a-z]+)\s+(\([A-Z][0-9],\s+)?\\cite[^{]+{(?P<ref>[^}]+)}")
    gll, in_gll, prevline, pregll = [], False, None, None
    lines = s.split('\n')
    for lineno, line in enumerate(lines):
        line = strip_tex_comment(line).strip()
        if r'\langinfo' in line:
            res = parse_langinfo(line)
            if res:
                linfo = (res, lineno)
        elif r'\ili{' in line:
            res = parse_ili(line)
            if res:
                linfo = (res, lineno)
                line = line.replace('()', '').strip()
        elif r'\il{' in line:
            res = parse_il(line)
            if res:
                linfo = (res, lineno)
                line, rem = line.split(r'\il{', maxsplit=1)
                line += rem.split('}', maxsplit=1)[1] if '}' in rem else ''
                line = line.replace('()', '').strip()
        elif ex_pattern.match(line):
            m = ex_pattern.match(line)
            linfo = ((m.group('lname'), '', m.group('ref')), lineno)

        m = glt_start.search(line)
        if m:
            if gll and len(gll) < 10:
                #
                # We may need to fix the gloss line:
                mm = longexampleandlanguage_pattern.search(gll[-1])
                if mm:
                    linfo = ((mm.groups()[0], '', ''), lineno)
                    gll[-1] = gll[-1][:mm.start()]
                pre = line[:m.start()]
                line = line[m.end() - (1 if m.groups()[1] else 0):]
                if not line:  # glt on a line by itself. We assume the next line is the translation.
                    line = lines[lineno + 1]
                gll.append(pre)
                gll.append(line)
                # Return linfo it wasn't parsed too far from the example:
                yield linfo[0] if linfo and (lineno - linfo[1] < 25) else None, gll, pregll
            gll, in_gll = [], False
            continue
        m = gll_start.search(line)
        if m:
            line = line[m.end() - 1:]
            gll, pregll = [], prevline
            in_gll = True
        if in_gll:
            gll.append(line)

        prevline = line


def recombine(morphemes):
    """
    For better visual alignment, morphemes in examples are sometimes whitespace-separated - making
    them appear as words. This function recombines morphemes into words according to leading and
    trailing LGR morpheme separators.
    """
    chunk = []
    for c in morphemes:
        if not c:
            continue
        if c[0] in MORPHEME_SEPARATORS or (chunk and chunk[-1][-1] in MORPHEME_SEPARATORS):
            chunk.append(c)
        else:
            if chunk:
                yield ''.join(chunk)
            chunk = [c]
    if chunk:
        yield ''.join(chunk)


def fixed_alignment(pt, gl):
    """
    Given the aligned lines of an LGR IGT example, we try a couple of tricks to make sure both lines
    have the same number of word chunks.
    """
    comment = None

    # pre-process
    # Merge multi-word lexical glosses:
    multi_word_gloss = re.compile(r'(\s|^){([Ia-z ]+|North Wales|The birds)}(\s|,|$)')
    gl = multi_word_gloss.sub(
        lambda m: ' {} '.format(re.sub(r'\s+', '_', m.groups()[1])), gl).strip()
    gl = re.sub(r'(\s|^){}(\s|$)', ' _ ', gl.replace('{} {}', '{}  {}'))
    gl = re.sub(r'(\s|^){}{}(\s|$)', ' _ ', gl)
    gl = re.sub(r'(\s|^)~(\s|$)', ' _ ', gl)

    # Merge multi-word primary text groups:
    for k, v in {
        'Adnominal clause': '(Adnominal_clause)',
        'Adverbial clause': '(Adverbial_clause)',
        'Adverbila clause': '(Adverbial_clause)',

    }.items():
        pt = pt.replace(k, v)
    for k, v in CHAR_REPLS.items():
        pt = pt.replace(k, v)
    multi_word_pt = re.compile(r'(\s|^|-){([\w žąį./]+)}(\s|\.|$)')
    pt = multi_word_pt.sub(
        lambda m: ' {} '.format(re.sub(r'\s+', '_', m.groups()[1])), pt).strip()
    pt = re.sub(r'(\s|^){}(\s|$)', ' _ ', pt)

    # de-latex
    pt = to_text(pt)[0].split()
    gl = to_text(gl)[0].split()

    # post-process
    ellipsis_variants = [
        '....', '[…]', '[...]', '...', '[...].', '“…”', '[…].', '(...).', '…]']
    pt = [ELLIPSIS if w in ellipsis_variants else w for w in pt]
    gl = [ELLIPSIS if w in ellipsis_variants else w for w in gl]

    if len(pt) > len(gl):
        if pt[-1] == '.':
            pt = pt[:-1]
            pt[-1] += '.'
        elif pt[-1] == '[]':
            pt = pt[:-1]

    ldiff = len(pt) - len(gl)
    if ldiff == -1:
        if gl and gl[-1].startswith('[') and gl[-1].endswith(']'):
            comment = gl[-1][1:-1].strip()
            gl = gl[:-1]
    elif ldiff == 1:
        if ELLIPSIS in pt:
            gl.insert(pt.index(ELLIPSIS), ELLIPSIS)
        elif '/' in pt:
            gl.insert(pt.index('/'), '/')
        elif EMPTY in pt:
            gl.insert(pt.index(EMPTY), EMPTY)
        elif EMPTY + '.' in pt:
            gl.insert(pt.index(EMPTY + '.'), EMPTY)
        elif pt[-1] in [']', '].', ']?']:
            gl.append('_')
        elif re.fullmatch(r'\([^)]+\)', pt[-1]):
            comment = pt[-1].replace('(', '').replace(')', '')
            pt = pt[:-1]

    ldiff = len(pt) - len(gl)
    if ldiff > 0:
        if ldiff == pt.count(ELLIPSIS):
            for i, c in enumerate(pt):
                if c == ELLIPSIS:
                    gl.insert(i, ELLIPSIS)
        elif ldiff == pt.count('<') + pt.count('>'):
            for i, c in enumerate(pt):
                if c in ['<', '>']:
                    gl.insert(i, '_')

    pt_r, gl_r = list(recombine(pt)), list(recombine(gl))
    if len(pt_r) == len(gl_r):
        pt, gl = pt_r, gl_r
    return pt, gl, comment


def lines_and_comment(lines):
    """
    Figure out which lines of all lines between \\gll and \\glt to be considered as
    word/morpheme-segmented primary text and gloss.

    :param lines:
    :return:
    """
    res, comment, linfo = [], [], None
    for line in lines:
        line = line.strip()
        if line:
            try:
                s = TexSoup(line, tolerance=1)
                if s.jambox:
                    comment.append(s.jambox.string)
                    s.jambox.delete()
                    line = str(s)
            except:  # noqa: E722
                pass  # pragma: no cover
            if line:
                res.append(line)

    if len(res) > 2:
        # Language names as second argument to "longexampleandlanguage" commands.
        m = re.fullmatch(r'}{([A-Z][a-z]+)}', res[-1].split('\n')[0])
        if m:
            linfo = (m.groups()[0], '', '')
            res = res[:-1]
        else:
            # Comments in square brackets appended to the example.
            m = re.fullmatch(r'\[([\w ]+)]', to_text(res[-1].split('\n')[0])[0].strip())
            if m:
                comment.append(m.groups()[0])
                res = res[:-1]
            else:
                # A single word: Considered a comment.
                m = re.fullmatch(r'([\w]+)', to_text(res[-1].split('\n')[0])[0].strip())
                if m:
                    comment.append(m.groups()[0])
                    res = res[:-1]
                else:
                    # Language names appended as special comment in parentheses to the example.
                    m = re.fullmatch(
                        r'\(?([A-Z][a-z]+(-English)?|[0-9/]+|[A-Z][A-Z]+)\)?',
                        to_text(res[-1].split('\n')[0])[0].strip())
                    if m:
                        if m.groups()[0][0].isalpha() and m.groups()[0][0].islower():
                            linfo = (m.groups()[0], '', '')
                        else:
                            comment.append(m.groups()[0])
                        res = res[:-1]
    return [r.replace('\n', ' ') for r in res], '; '.join(comment), linfo


def make_example(
        pub: Publication,
        linfo: typing.Tuple[str, str, str],
        gll: typing.List[str],
        prevline: str) -> typing.Optional[Example]:
    _, _, refs = to_text(prevline)
    comment = []
    if linfo:
        linfo = [to_text(s or '')[0] for s in linfo]
        if linfo[2]:
            comment.append(linfo[2])

    lname = linfo[0] if linfo and linfo[0] else None

    #
    # At this point `gll` is just a bunch of text lines containing latex formatting.
    #
    # We assume the last text line to be the translation ...
    aligned, translation = '\n'.join(gll[:-1]), gll[-1]
    translation, cmt, _refs = to_text(translation)
    if _refs:
        refs.extend(_refs)
    if cmt:
        comment.append(cmt)

    # ... and split the remainder at latex newlines:
    aligned = [line.strip() for line in re.split(r'\\(?:\\|newline)', aligned) if line.strip()]

    # book-specifics:
    if pub.record.int_id == 212:
        if len(aligned) > 2:
            if 'footnotesize' in aligned[2]:
                aligned = aligned[:2]

    aligned, cmt, linfo2 = lines_and_comment(aligned)
    if linfo2 and linfo2[0]:
        lname = linfo2[0]
    if cmt:
        comment.append(cmt)

    al = []
    for line in aligned:
        delatexed, cmt, _refs = to_text(line)
        if _refs:
            refs.extend(_refs)
        if cmt:
            comment.append(cmt)
        if delatexed.replace('*', '').strip():  # Not an empty line (when texed).
            al.append(line)
    aligned = al

    if len(aligned) == 3:
        # There's a separate line for the morpheme-segmented primary text!
        obj, pt, gl = aligned
    elif len(aligned) == 2:
        pt, gl = aligned
        obj = None
    elif len(aligned):
        if len(aligned) == 4 and aligned[3].startswith(r'}\\jambox'):
            obj, pt = aligned[0], aligned[1]
            gl = aligned[2] + aligned[3]
        else:  # Dunno what to do here ...
            # print(filename)
            # print(len(aligned), aligned)
            # print('---')
            return
    else:  # ... or here.
        return
    if obj:
        obj, cmt, _refs = to_text(obj)
        if _refs:
            refs.extend(_refs)
        if cmt:
            comment.append(cmt)

    pt, gl, cmt = fixed_alignment(pt, gl)
    if cmt:
        comment.append(cmt)
    if len(pt) != len(gl):
        if gl and gl[-1] in ['()', '*()']:
            gl = gl[:-1]
    if len(pt) != len(gl):
        return

    obj = obj or IGT(phrase=pt, gloss=gl).primary_text
    return Example(
        ID=hashlib.sha256(obj.replace('.', '').encode('utf8')).hexdigest()[:10],
        Primary_Text=obj,
        Analyzed_Word=pt,
        Gloss=gl,
        Translated_Text=translation,
        Language_Name=lname if len(lname or '') > 2 else None,
        Comment=comment,
        Source=refs,
    )
