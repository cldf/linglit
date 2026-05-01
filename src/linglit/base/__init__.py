import re
import pathlib
import functools
import collections
from collections.abc import Generator
import dataclasses
from typing import Optional, Union

from pyigt import IGT
from pycldf.sources import Source
from pyglottolog import Glottolog as API

from linglit.util import clean_translation

__all__ = ['Glottolog', 'Record', 'Repository', 'Publication', 'Example']


class Glottolog:
    def __init__(self, glottolog: Union[str, pathlib.Path, API]):
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

    def register_names(self, names: dict[str, str]):
        self.by_name = {k: v for k, v in self._by_name.items()}
        for k, v in names.items():
            if v:
                v = self(v)
                if v:
                    self.by_name[k] = self.by_glottocode[v]

    def __call__(self, name: str) -> Optional[str]:
        if name:
            if name in self.by_glottocode:
                return self.by_glottocode[name].id
            if name in self.by_isocode:
                return self.by_isocode[name].id
            gl = self.by_name.get(name)
            if gl:
                return gl.id


@dataclasses.dataclass
class Record:
    """
    Metadata record for a publication.
    """
    ID: str
    DOI: str
    metalanguage: Optional[str]
    objectlanguage: Optional[str]
    license: str
    creators: str
    title: str
    year: str

    def __post_init__(self):
        assert re.fullmatch(r'[0-9]+', self.ID)

    def as_source(self) -> Source:  # pragma: no cover
        raise NotImplementedError()

    @property
    def has_open_license(self) -> bool:
        return any(self.license.split()[0] == s for s in ['CC-BY', 'CC-BY-SA'])

    @property
    def current(self) -> bool:
        return True

    @property
    def int_id(self) -> int:
        return int(self.ID)


@dataclasses.dataclass
class Example:
    ID: str
    Primary_Text: str
    Analyzed_Word: list[str]
    Gloss: list[str]
    Translated_Text: str
    Language_Name: str
    Comment: str
    Source: list[str]
    Language_ID: Optional[str] = None
    Source_Path: Optional[str] = None
    Abbreviations: dict[str, str] = dataclasses.field(default_factory=collections.OrderedDict)
    Local_ID: Optional[str] = None
    Meta_Language_ID: Optional[str] = None
    Corpus_Ref: Optional[str] = None

    def __post_init__(self):
        assert isinstance(self.Analyzed_Word, list)
        assert isinstance(self.Gloss, list)
        self.Translated_Text = clean_translation(self.Translated_Text)
        assert isinstance(self.Source, list)
        self.Comment = '; '.join(self.Comment) if isinstance(self.Comment, list) else self.Comment

        if self.Translated_Text.endswith(']') and self.Translated_Text.count('[') == 1:
            tt, _, cmt = self.Translated_Text[:-1].partition('[')
            if cmt not in ['…']:
                self.Translated_Text = clean_translation(tt.strip())
                cmt = cmt.strip()
                if len(cmt.split()) > 1:
                    if self.Comment:
                        self.Comment += '; '
                    self.Comment = (self.Comment or '') + cmt
                else:
                    self.Corpus_Ref = cmt

    def __str__(self):
        res = f'({self.Local_ID or self.ID})'
        if self.Language_Name:
            res += f' {self.Language_Name}'
        if self.Source:
            res += ' ('
            for i, (sid, pages) in enumerate(self.Source):
                if i:
                    res += '; '
                res += sid
                if pages:
                    res += f': {pages}'
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


class Publication:
    def __init__(self, record: Record, d: Union[str, pathlib.Path], repos=None):
        self.record = record
        self.dir = pathlib.Path(d)
        self.repos = repos

    def __str__(self):
        return f"{self.record.creators} {self.record.year}. {self.record.title}"

    @property
    def is_current(self) -> bool:
        return self.record.current

    @property
    def has_open_license(self) -> bool:
        return self.record.has_open_license

    @functools.cached_property
    def cited_references(self) -> list[Source]:
        return [ref for ref in self.references.values() if ref.id in self.cited]

    @functools.cached_property
    def id(self) -> str:
        return f'{self.repos.id}{self.record.int_id}'

    def as_source(self) -> Source:
        src = self.record.as_source()
        src.id = self.id
        return src

    @functools.cached_property
    def references(self) -> collections.OrderedDict[str, Source]:
        res = collections.OrderedDict()
        for src in self.iter_references():
            sid = f'{self.id}:{src.id}'
            src['isreferencedby'] = self.id
            res[sid] = Source(src.genre, sid, _check_id=False, **src)
        return res

    def iter_references(self) -> Generator[Source, None, None]:  # pragma: no cover
        raise NotImplementedError()

    @functools.cached_property
    def cited(self) -> collections.Counter:
        res = collections.Counter()
        for key in self.iter_cited():
            res.update(['{}:{}'.format(self.id, key)])
        return res

    def iter_cited(self) -> Generator[str, None, None]:  # pragma: no cover
        raise NotImplementedError()

    def example_sources(self, ex: Example) -> list[Source]:
        """
        Resolve the source IDs for an example to `Source` instances.
        """
        return [self.references[sid] for sid, _ in ex.Source if sid != self.id] + [self.as_source()]

    @functools.cached_property
    def examples(self):
        res = []
        for ex in self.iter_examples():
            ex.ID = f'{self.id}-{ex.ID}'
            refs = []
            for sid, pages in ex.Source:
                refs.append((f'{self.id}:{sid}', pages))
            if refs:
                pages = 'via'
                if ex.Local_ID:
                    pages += f':{ex.Local_ID}'
                refs.append((self.id, pages))
            else:
                refs.append((self.id, ex.Local_ID))
            ex.Source = refs
            res.append(ex)
        return res

    def iter_examples(self) -> Generator[Example, None, None]:  # pragma: no cover
        raise NotImplementedError()


class Repository:
    id = None
    lname_map = {}

    def __init__(self, d):
        self.dir = pathlib.Path(d)

    def __getitem__(self, item: str) -> Publication:  # pragma: no cover
        raise NotImplementedError()

    def path(self, *comps):
        return self.dir.joinpath(*comps)

    def create(self, verbose=False):  # pragma: no cover
        raise NotImplementedError()

    def iter_publications(self):  # pragma: no cover
        raise NotImplementedError()
