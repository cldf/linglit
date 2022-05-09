import collections

import attr
from clldutils.misc import lazyproperty
from pycldf.sources import Source

from linglit import base
from . import xml


@attr.s
class Record(base.Record):
    doc = attr.ib()

    def as_source(self):
        return Source(
            'article',
            '{}'.format(self.ID),
            author=self.creators,
            title=self.title,
            year=self.year,
            volume=self.doc.xpath(".//volume")[0].text,
            issue=self.doc.xpath(".//issue")[0].text,
            doi=self.DOI,
            publisher="Open Library of Humanities",
            journal="Glossa: a journal of general linguistics",
        )

    @property
    def has_open_license(self):
        return True


class Publication(base.Publication):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.doc = xml.parse(self.dir)
        self.language_spec = self.record
        self.record=Record(**xml.metadata(self.dir, self.doc))
        self.abbreviations=xml.abbreviations(self.doc)

    @lazyproperty
    def references(self):
        return collections.OrderedDict([(s.id, s) for s in xml.refs(self.doc)]),

    @property
    def cited(self):
        raise NotImplementedError()

    def iter_examples(self, glottolog=None):
        for count, number, letter, lang, xrefs, igt in xml.iter_igt(self.doc, self.abbreviations):
            lid = '{}{}'.format(number or '', letter or '')
            refs = []
            for sid, reft, label in xrefs:
                if reft == 'bibr':
                    pages = label.partition(':')[2].strip() if label else ''
                    refs.append((sid, pages.replace('[', '(').replace(']', ')')))
            #if refs:
            #    refs.append((self.record.id, 'via:{}'.format(lid)))
            #else:
            #    refs.append((self.record.id, lid))

            yield base.Example(
                ID='{}-{}'.format(self.record.ID, count),
                Local_ID=lid,
                Primary_Text=igt.primary_text,
                Analyzed_Word=igt.phrase,
                Gloss=igt.gloss,
                Translated_Text=igt.translation,
                Language_ID=None,
                Language_Name=self.language_spec(lang, lid) if self.language_spec else lang,
                Comment=None,
                Source=refs,
                Abbreviations=self.abbreviations,
            )
