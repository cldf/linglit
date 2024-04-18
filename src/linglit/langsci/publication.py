import re
import functools
import collections

from clldutils.path import walk

from linglit import base
from .bibtex import iter_bib, normalize_key
from .texsoup import iter_texsoup_lines
from .latex import to_text, iter_abbreviations
from . import texfixes
from .examples import iter_gll, make_example
from . import cfg

MAKEFILE_NAME = 'Makefile'
MAIN_TEX_NAMES = ['main.tex', 'book.tex']
BACKMATTER_NAME = 'backmatter.tex'
ABBREVIATIONS_NAME = 'abbreviations.tex'
CHAPTERS_NAME = 'chapters'
MAIN_TEX_EXCEPTIONS = {  # Cases where the main TeX file can't be found:
    49: 'ind-steelsbook.tex',
}
NO_BIB = [274]
NO_INCLUDES = [163]
FIX_FILENAMES = {
    'parts/bilinguismo': 'parts/biblinguismo',
}


class Publication(base.Publication):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        if self.record.int_id in MAIN_TEX_EXCEPTIONS:  # pragma: no cover
            main = self.dir / MAIN_TEX_EXCEPTIONS[self.record.int_id]
        else:
            main = self._find_main_tex()
        assert main, self.record.ID
        self.main = main

        self._bibs = None
        self._includes = None
        self._includes_tex = {}
        self._refs = []

    def iter_examples(self):
        texfile2language = {}
        for row in cfg.iter_texfile_titles():
            if row['Language']:
                texfile2language[(int(row['Book_ID']), row['Filename'])] = row['Language']
        seen = set()
        for p in self.includes:
            for linfo, gll, prevline in iter_gll(self.read_tex(p)):
                ex = make_example(self, linfo, gll, prevline)
                if ex and (ex.ID not in seen):
                    ex.Source_Path = p
                    if self.repos:
                        ex.Source_Path = p.relative_to(self.repos.dir)
                    refs = []
                    for key, pages in ex.Source:
                        key = normalize_key(key)
                        if key in self.bibkeys:
                            refs.append((self.bibkeys[key], pages))
                    ex.Source = refs
                    if ex.Language_Name is None and \
                            (self.record.int_id, p.name) in texfile2language:
                        ex.Language_Name = texfile2language[(self.record.int_id, p.name)]
                    if ex.Language_Name is None and self.record.objectlanguage:
                        ex.Language_Name = self.record.objectlanguage
                    if str(p) in self.gloss_abbreviations:
                        ex.Abbreviations = self.gloss_abbreviations[str(p)]
                    elif None in self.gloss_abbreviations:
                        ex.Abbreviations = self.gloss_abbreviations[None]
                    ex.Meta_Language_ID = self.record.metalanguage
                    seen.add(ex.ID)
                    yield ex

    def iter_cited(self):
        relevant = self.includes + [self.main]
        if self.main.parent.joinpath(BACKMATTER_NAME).exists():
            relevant.append(self.main.parent.joinpath(BACKMATTER_NAME))
        for p in relevant:
            for line in self.read_tex(p, with_input=(p != self.main)).split(r'\\'):
                _, _, refs = to_text(line)
                for ref, _ in refs:
                    key = normalize_key(ref)
                    if key in self.bibkeys:
                        yield self.bibkeys[key]

    def iter_references(self):
        if not self._refs:
            self._refs = list(iter_bib(self.bibs))
        yield from iter(self._refs)

    # --- langsci specifics
    def read_tex(self, p, with_input=True):
        if str(p) not in self._includes_tex:
            self._includes_tex[str(p)] = texfixes.read_tex(p, with_input=with_input)
        return self._includes_tex[str(p)]

    @functools.cached_property
    def gloss_abbreviations(self):
        abbr_pattern = re.compile(r'\\(sub)?section\*?(\[[^]]+])?{Abbreviations(\s+[A-Za-z]+)*}')
        section_pattern = re.compile(r'\\(?:sub)?section')
        res = collections.defaultdict(collections.OrderedDict)

        for p in self.includes:
            tex = self.read_tex(p)
            m = abbr_pattern.search(tex)
            if m:
                for k, v in iter_abbreviations(section_pattern.split(tex[m.end():])[0]):
                    res[str(p)][k] = v

        for p in walk(self.dir):
            if p.name == ABBREVIATIONS_NAME:
                for k, v in iter_abbreviations(self.read_tex(p)):
                    res[None][k] = v

        return res

    def _get_includes_and_bibs(self):
        self._includes, self._bibs = includes_and_bib(
            self.dir,
            self.main,
            CHAPTERS_NAME if self.main.parent.joinpath(CHAPTERS_NAME).exists() else 'indexed',
            no_bib=self.record.int_id in NO_BIB,
        )

    @property
    def bibs(self):
        if self._bibs is None:
            self._get_includes_and_bibs()  # pragma: no cover
        return self._bibs

    @functools.cached_property
    def bibkeys(self):
        res = {}
        for src in self.iter_references():
            res[src.id] = src.id
            for altkey in src.alt_keys:
                res[altkey] = src.id
        return res

    @property
    def includes(self):
        if self._includes is None:
            self._get_includes_and_bibs()
        return self._includes

    def _find_makefile(self):
        p = self.dir / MAKEFILE_NAME
        if p.exists():
            return p
        for p in walk(self.dir, mode='files'):
            if p.name == MAKEFILE_NAME:
                return p

    def _find_by_documentclass(self, d):
        for p in d.glob('*.tex'):
            for line in p.read_text(encoding='utf8').split('\n'):
                if all(w in line for w in [r'\documentclass', 'number']):
                    return p

    def _find_main_tex(self):
        make = self._find_makefile()
        if make:
            for line in make.read_text(encoding='utf8').splitlines():
                line = line.strip()
                if line.startswith('xelatex'):
                    tex = '{}.tex'.format(line.split()[-1])
                    if tex and make.parent.joinpath(tex).exists():
                        return make.parent / tex
            for line in make.read_text(encoding='utf8').splitlines():
                pdf = re.search(r'\s+([A-Za-z_0-9]+)\.pdf(\s|$)', line.strip(), flags=re.MULTILINE)
                if pdf:
                    tex = '{}.tex'.format(pdf.groups()[0])
                    if tex and make.parent.joinpath(tex).exists():
                        return make.parent / tex
        for name in MAIN_TEX_NAMES:
            if self.dir.joinpath(name).exists():
                return self.dir / name
        subdirs = [sd for sd in self.dir.iterdir() if sd.is_dir()]
        if len(subdirs) == 1 and not list(self.dir.glob('*.tex')):
            # All the main sources are nested in one directory.
            for name in MAIN_TEX_NAMES:
                if subdirs[0].joinpath(name).exists():
                    return subdirs[0] / name
        p = self._find_by_documentclass(self.dir)
        if p:
            return p
        for sd in subdirs:
            p = self._find_by_documentclass(sd)
            if p:
                return p


def includes_and_bib(d, main, chapterpath, no_bib):
    def norm_include(s):
        s = s.replace('\\chpath', chapterpath) \
            .replace('\\chapterpath', chapterpath) \
            .replace('\\folder', chapterpath)
        s = FIX_FILENAMES.get(s, s)
        if not s.endswith('.tex'):
            s += '.tex'
        return s

    tex = main.read_text(encoding='utf8')
    tex = tex.replace(r'\input{chapters/', r'\include{chapters/')
    tex = tex.replace(r'\input{phrasal-lfg-include', r'\include{phrasal-lfg-include')
    tex_lines = list(iter_texsoup_lines(main, tex=tex))
    for pincl in main.parent.glob('*-include.tex'):
        tex_lines.extend(iter_texsoup_lines(pincl))

    # Three variants of bib detection:
    bibs = [p for p in d.glob('*.bib')]
    if no_bib:  # explicitly marked as not having a bib
        bibs = []  # pragma: no cover
    elif len(bibs) == 1:  # only one choice for bibs
        pass  # pragma: no cover
    else:  # more bib files available, pick by parsing the main tex file
        bibs, bibnames = [], []
        for soup in tex_lines:
            if soup.bibliography or soup.addbibresource:
                bibnames.extend((soup.bibliography or soup.addbibresource).string.split(','))
        assert bibnames, str(main)
        for name in bibnames:
            if not name.endswith('.bib'):
                name += '.bib'
            bib = main.parent / name
            assert bib.exists(), str(bib)
            bibs.append(bib)
    includes = []

    for soup in tex_lines:
        incl = soup.include or soup.includechapter or soup.includepaper
        if incl:
            p = main.parent / norm_include(incl.string)
            # Allow case-insensitive matching:
            m = {pp.name.lower(): pp for pp in p.parent.glob('*.tex')}
            p = m.get(p.name.lower(), p)
            if not p.exists() and (p.stem in ['preface', 'acknowledgments']):
                continue
            if not p.exists() and p.stem == 'abbreviations':
                if p.parent.parent.joinpath('abbreviations.tex').exists():
                    p = p.parent.parent.joinpath('abbreviations.tex')
            assert p.exists(), str(p)
            includes.append(p)
    return includes, bibs
