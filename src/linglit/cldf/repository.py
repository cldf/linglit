import shutil
import functools
import collections

import attr
import cldfzenodo
from clldutils.jsonlib import dump, load
from pycldf import Source
from csvw.dsv import reader

from linglit import base
from .publication import Publication


@attr.s
class Record(base.Record):
    bibtex = attr.ib()

    def as_source(self):
        return Source.from_bibtex(self.bibtex)


@attr.s
class Dataset:
    """
    A row in a repository's catalog.csv file.
    """
    id = attr.ib()
    name = attr.ib()
    conceptdoi = attr.ib()
    source_to_language = attr.ib()
    hhtype = attr.ib()
    bib = attr.ib(converter=lambda s: bool(s))
    igt = attr.ib(converter=lambda s: bool(s))
    gloss_abbreviations = attr.ib(converter=lambda s: s.split())  # triple (fname, abbrcol, defcol)


class Repository(base.Repository):
    id = 'cldf'

    @functools.cached_property
    def catalog(self):
        return collections.OrderedDict([
            (row['name'], Dataset(**row)) for row in reader(self.dir / 'catalog.csv', dicts=True)])

    def __getitem__(self, did):
        md = self.metadata(did)
        return Publication(
            Record(
                ID=str(self.catalog[did].id),
                DOI=md['doi'],
                license=md['license'],
                creators=md['creators'],
                title=md['title'],
                year=md['year'],
                metalanguage=None,
                objectlanguage=None,
                bibtex=cldfzenodo.Record(**md).bibtex,
            ),
            self.dir / did,
            self)

    def metadata(self, did):
        return load(self.dir / '{}.json'.format(did))

    def iter_publications(self):
        for i, (did, rmd) in enumerate(self.catalog.items(), start=1):
            md = self.metadata(did)
            yield Publication(
                Record(
                    ID=str(rmd.id),
                    DOI=md['doi'],
                    license=md['license'],
                    creators=md['creators'],
                    title=md['title'],
                    year=md['year'],
                    metalanguage=None,
                    objectlanguage=None,
                    bibtex=cldfzenodo.Record(**md).bibtex,
                ),
                self.dir / did,
                self)

    def create(self, verbose=False):
        for did, dataset in self.catalog.items():
            dldir = self.dir / did
            print(did)
            rec = cldfzenodo.Record.from_concept_doi(dataset.conceptdoi)
            if dldir.exists():
                if self.metadata(did)['version'] == rec.version:
                    continue
                shutil.rmtree(dldir)
            print('downloading {} ...'.format(rec.version))
            rec.download_dataset(self.dir / did)
            print('... done')
            dump(attr.asdict(rec), self.dir / '{}.json'.format(did), indent=2)
