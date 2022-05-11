import re
import pathlib

PKG_PATH = pathlib.Path(__file__).parent
CFG_PATH = PKG_PATH / 'cfg'
STARTINGQUOTE = "`‘“"
ENDINGQUOTE = "'’”"
ELLIPSIS = '…'


def clean_translation(trs):
    trs = re.sub(r'\s+', ' ', trs.strip())
    try:
        if trs[0] in STARTINGQUOTE:
            trs = trs[1:]
        if trs[-1] in ENDINGQUOTE:
            trs = trs[:-1]
        if len(trs) > 1 and (trs[-2] in ENDINGQUOTE) and (trs[-1] == '.'):
            trs = trs[:-2] + '.'
        trs = trs.replace("()", "")
    except IndexError:  # s is  ''
        pass
    trs = trs.replace('...', ELLIPSIS)
    return trs
