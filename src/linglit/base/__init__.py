import re
import pathlib
import collections

import attr
from pyigt import IGT
from clldutils.source import Source

STARTINGQUOTE = "`‘"
ENDINGQUOTE = "'’"
ELLIPSIS = '…'


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

    def as_source(self) -> Source:
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

    def create(self):
        raise NotImplementedError()

    def iter_publications(self):
        raise NotImplementedError()

    def register_language_names(self, glottolog):
        return


class Publication:
    def __init__(self, record, d, repos=None):
        self.record = record
        self.dir = pathlib.Path(d)
        self.repos = repos

    def as_source(self):
        src = self.record.as_source()
        src.id = '{}:{}'.format(self.repos.id, src.id)
        return src

    @property
    def references(self) -> collections.OrderedDict:
        raise NotImplementedError()

    @property
    def cited(self) -> collections.Counter:
        raise NotImplementedError()

    def iter_examples(self):
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
    Comment = attr.ib()
    Source = attr.ib(validator=attr.validators.instance_of(list))
    Language_ID = attr.ib(default=None)  # Assigned after initialization based on Language_Name
    Source_Path = attr.ib(default=None)
    Abbreviations = attr.ib(default=attr.Factory(collections.OrderedDict))
    Local_ID = attr.ib(default=None)

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
