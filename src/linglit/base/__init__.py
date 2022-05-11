import re
import typing
import pathlib
import collections

import attr
from pyigt import IGT
from pycldf.sources import Source
from clldutils.misc import lazyproperty
from pyglottolog import Glottolog as API

STARTINGQUOTE = "`‘"
ENDINGQUOTE = "'’"
ELLIPSIS = '…'


class Glottolog:
    def __init__(self, glottolog):
        if not isinstance(glottolog, API):  # pragma: no cover
            glottolog = API(glottolog)
        self.by_glottocode = {}
        self.by_isocode = {}
        self._by_name = {}
        self.by_custom_name = {}

        for lg in glottolog.languoids():
            self.by_glottocode[lg.id] = lg
            if lg.iso:
                self.by_isocode[lg.iso] = lg
            self._by_name[lg.name] = lg
            for _, names in lg.names.items():
                for name in names:
                    name = name.split('[')[0].strip()
                    if name not in self._by_name:
                        self._by_name[name] = lg

        self.by_name = {k: v for k, v in self._by_name.items()}
        self.api = glottolog

    def register_names(self, names):
        self.by_name = {k: v for k, v in self._by_name.items()}
        for k, v in names.items():
            if v:
                self.by_name[k] = self.by_glottocode[v]

    def __call__(self, name):
        if name:
            if name in self.by_glottocode:
                return self.by_glottocode[name].id
            if name in self.by_isocode:
                return self.by_isocode[name].id
            gl = self.by_name.get(name)
            if gl:
                return gl.id


@attr.s
class Record:
    ID = attr.ib(validator=attr.validators.matches_re(r'^[0-9]+$'))
    DOI = attr.ib()
    metalanguage = attr.ib()
    objectlanguage = attr.ib()
    license = attr.ib()
    creators = attr.ib()
    title = attr.ib()
    year = attr.ib()

    def as_source(self) -> Source:  # pragma: no cover
        raise NotImplementedError()

    @property
    def has_open_license(self) -> bool:
        return self.license in ['CC-BY', 'CC-BY-SA']

    @property
    def current(self) -> bool:
        return True

    @property
    def int_id(self) -> int:
        return int(self.ID)


class Repository:
    id = None

    def __init__(self, d):
        self.dir = pathlib.Path(d)

    def __getitem__(self, item):  # pragma: no cover
        raise NotImplementedError()

    def create(self, verbose=False):  # pragma: no cover
        raise NotImplementedError()

    def iter_publications(self):  # pragma: no cover
        raise NotImplementedError()

    def register_language_names(self, glottolog):
        return


class Publication:
    def __init__(self, record, d, repos=None):
        self.record = record
        self.dir = pathlib.Path(d)
        self.repos = repos

    def __str__(self):
        return "{0.creators} {0.year}. {0.title}".format(self.record)

    @lazyproperty
    def cited_references(self):
        return [ref for ref in self.references.values() if ref.id in self.cited]

    @lazyproperty
    def id(self):
        return '{}{}'.format(self.repos.id, self.record.ID)

    def as_source(self):
        src = self.record.as_source()
        src.id = self.id
        return src

    @lazyproperty
    def references(self) -> collections.OrderedDict:
        res = collections.OrderedDict()
        for src in self.iter_references():
            sid = '{}:{}'.format(self.id, src.id)
            res[sid] = Source(src.genre, sid, _check_id=False, **src)
        return res

    def iter_references(self) -> typing.Generator[Source, None, None]:  # pragma: no cover
        raise NotImplementedError()

    @lazyproperty
    def cited(self) -> collections.Counter:
        res = collections.Counter()
        for key in self.iter_cited():
            res.update(['{}:{}'.format(self.id, key)])
        return res

    def iter_cited(self):  # pragma: no cover
        raise NotImplementedError()

    def example_sources(self, ex):
        return [self.references[sid] for sid, _ in ex.Source if sid != self.id] + [self.as_source()]

    @lazyproperty
    def examples(self):
        res = []
        for ex in self.iter_examples():
            ex.ID = '{}-{}'.format(self.id, ex.ID)
            refs = []
            for sid, pages in ex.Source:
                refs.append(('{}:{}'.format(self.id, sid), pages))
            if refs:
                pages = 'via'
                if ex.Local_ID:
                    pages += ':{}'.format(ex.Local_ID)
                refs.append((self.id, pages))
            else:
                refs.append((self.id, ex.Local_ID))
            ex.Source = refs
            res.append(ex)
        return res

    def iter_examples(self):  # pragma: no cover
        raise NotImplementedError()


def clean_translation(trs):
    trs = re.sub(r'\s+', ' ', trs.strip())
    try:
        if trs[0] in STARTINGQUOTE:
            trs = trs[1:]
        if trs[-1] in ENDINGQUOTE:
            trs = trs[:-1]
        if len(trs) > 1 and (trs[-2] in ENDINGQUOTE) and (trs[-1] == '.'):
            trs = trs[:-2]
        trs = trs.replace("()", "")
    except IndexError:  # s is  ''
        pass
    trs = trs.replace('...', ELLIPSIS)
    return trs


@attr.s
class Example:
    ID = attr.ib()
    Primary_Text = attr.ib()
    Analyzed_Word = attr.ib(validator=attr.validators.instance_of(list))
    Gloss = attr.ib(validator=attr.validators.instance_of(list))
    Translated_Text = attr.ib(converter=clean_translation)
    Language_Name = attr.ib()
    Comment = attr.ib(converter=lambda s: '; '.join(s) if isinstance(s, list) else s)
    Source = attr.ib(validator=attr.validators.instance_of(list))
    Language_ID = attr.ib(default=None)  # Assigned after initialization based on Language_Name
    Source_Path = attr.ib(default=None)
    Abbreviations = attr.ib(default=attr.Factory(collections.OrderedDict))
    Local_ID = attr.ib(default=None)
    Meta_Language_ID = attr.ib(default=None)

    def __str__(self):
        res = '({})'.format(self.Local_ID or self.ID)
        if self.Language_Name:
            res += ' {}'.format(self.Language_Name)
        if self.Source:
            res += ' ('
            for i, (sid, pages) in enumerate(self.Source):
                if i:
                    res += '; '
                res += sid
                if pages:
                    res += ': {}'.format(pages)
            res += ')'
        res += '\n'
        res += str(self.as_igt())
        return res

    def as_igt(self):
        return IGT(
            id=self.ID,
            phrase=self.Analyzed_Word,
            gloss=self.Gloss,
            translation=self.Translated_Text,
            abbrs=self.Abbreviations,
        )

    @property
    def coordination(self):
        for type_ in [' and ', ' or ']:
            if type_ in self.Translated_Text:
                return type_.strip()

    def _aspect(self, *types):
        for marker, type_ in types:
            if marker in self.Translated_Text.lower():
                return type_

    @property
    def time(self):
        return self._aspect((' yesterday ', 'past'), (' tomorrow ', 'future'), (' now ', 'present'))

    @property
    def modality(self):
        return self._aspect((' want ', 'volitive'))

    @property
    def polarity(self):
        return self._aspect((' not ', 'negative'))
