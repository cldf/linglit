import re

from csvw.dsv import reader
from pyglottolog.languoids import Glottocode

from linglit import util

CFG_PATH = util.CFG_PATH / 'glossa'
LNAME_MAP = {
    'Medieval Spanish': 'Old Spanish',
}


def language_specs():
    res = {}
    for d in reader(CFG_PATH / 'glossa.csv', dicts=True):
        if d['example_languages']:
            res[int(d['id'])] = LanguageSpec(d['example_languages'])
    return res


class LanguageSpec:
    def __init__(self, spec):
        self.language_ranges = {}
        self.language = None
        if spec.strip():
            chunks = [s.strip() for s in spec.split(',')]
            if len(chunks) == 1 and Glottocode.pattern.fullmatch(chunks[0]):
                self.language = chunks[0]
            elif chunks:
                for chunk in chunks:
                    glottocode, _, range = chunk.partition(':')
                    glottocode = glottocode.strip()
                    assert Glottocode.pattern.fullmatch(glottocode)
                    lower, _, upper = range.partition('-')
                    lower = int(lower) if lower.strip() else 0
                    upper = int(upper) if upper.strip() else 1000
                    self.language_ranges[glottocode] = (lower, upper)

    def __call__(self, name, lid):
        # 1. Check, if ex has already a resolvable Language_Name
        if name:
            return name
        if self.language:
            return self.language
        if self.language_ranges:
            # Get the numeric part of the local ID
            m = re.match(r'[0-9]+', lid)
            if m:
                lid = int(lid[:m.end()])
                for gc, (min, max) in self.language_ranges.items():
                    if min <= lid <= max:
                        return gc
