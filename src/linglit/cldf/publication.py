import functools
import collections

from pycldf.dataset import iter_datasets
from pycldf.sources import Sources
from pyigt import Example

from linglit import base


class Publication(base.Publication):
    @functools.cached_property
    def ds(self):
        return next(iter_datasets(self.dir))

    @functools.cached_property
    def cfg(self):
        return self.repos.catalog[self.dir.name]

    @functools.cached_property
    def languages(self):
        return self.ds.objects('LanguageTable')

    def iter_references(self):
        sid2langs = collections.defaultdict(set)
        if not self.cfg.bib:
            return
        s2l = self.cfg.source_to_language
        l2gc = {}
        for row in self.languages:
            if row.cldf.glottocode:
                l2gc[row.id] = row.cldf.glottocode
                if s2l == 'LanguageTable':
                    for src in row.cldf.source:
                        sid, _ = Sources.parse(src)
                        sid2langs[sid].add(row.cldf.glottocode)
        if s2l == 'ValueTable':
            for row in self.ds.iter_rows('ValueTable', 'languageReference', 'source'):
                if row['languageReference'] in l2gc:
                    for src in row['source']:
                        sid, _ = Sources.parse(src)
                        sid2langs[sid].add(l2gc[row['languageReference']])
        for src in self.ds.sources:
            for field in [
                'besttxt', 'cfn', 'delivered', 'fn',
                'languageid', 'glottolog_ref_id', 'glottolog_ref',
                'gbid', 'google_book_search_id', 'google_book_search_viewability',
                'google_book_viewability',
            ]:
                if field in src:
                    del src[field]
            if src.id in sid2langs:
                src['lgcode'] = '; '.join('[{}]'.format(gc) for gc in sorted(sid2langs[src.id]))
            if self.cfg.hhtype:
                src['hhtype'] = self.cfg.hhtype
            yield src

    def iter_cited(self):
        for src in self.ds.sources:
            yield src.id

    def iter_examples(self, glottolog=None):
        abbrs = {}
        if self.cfg.gloss_abbreviations:
            fname, abbrcol, defcol = self.cfg.gloss_abbreviations
            abbrs = collections.OrderedDict(
                [(r[abbrcol], r[defcol]) for r in self.ds.iter_rows(fname)])
        l2gc = {lg.id: (lg.cldf.glottocode, lg.cldf.name) for lg in self.languages}
        if self.cfg.igt:
            for count, ex in enumerate(self.ds.objects('ExampleTable', cls=Example), start=1):
                if abbrs:
                    ex.igt.abbrs = abbrs
                if ex.igt.primary_text and ex.igt.phrase:
                    yield base.Example(
                        ID='{}'.format(count),
                        Local_ID=ex.id,
                        Primary_Text=ex.igt.primary_text,
                        Analyzed_Word=ex.igt.phrase,
                        Gloss=ex.igt.gloss,
                        Translated_Text=ex.igt.translation or '',
                        Language_ID=l2gc[ex.cldf.languageReference][0],
                        Language_Name=l2gc[ex.cldf.languageReference][1],
                        Source=[],
                        Abbreviations=ex.igt.gloss_abbrs if ex.igt.is_valid(strict=True) else {},
                        Meta_Language_ID=ex.cldf.metaLanguageReference or 'stan1293',
                        Comment=getattr(ex.cldf, 'comment', None),
                    )
