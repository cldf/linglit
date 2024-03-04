import io
import urllib.request

import attr
from csvw.dsv import reader, UnicodeWriter
from pycldf.sources import Source

from linglit import base

URL = "https://raw.githubusercontent.com/langsci/opendata/master/catalog.csv"
GITHUB_ORG = 'langsci'


@attr.s
class Record(base.Record):
    edited = attr.ib()
    superseded = attr.ib()
    pages = attr.ib()
    series = attr.ib()
    seriesnumber = attr.ib()

    @property
    def current(self):
        return self.superseded != 'True'

    def as_source(self):
        md = dict(
            title=self.title,
            year=self.year,
            series=self.series,
            number=self.seriesnumber,
            address="Berlin",
            publisher="Language Science Press",
            doi=self.DOI,
        )
        parts = [ss.strip() for ss in self.creators.replace(' & ', ',').split(',')]
        assert len(parts) % 2 == 0, 'Odd number of commas: {}'.format(self.creators)
        names = ' and '.join(['{}, {}'.format(*parts[i:i + 2]) for i in range(0, len(parts), 2)])
        names = names.replace('\u180e', '').strip()
        if names.endswith(','):
            names = names[:-1].strip()
        if self.edited:
            md['editor'] = names
        else:
            md['author'] = names
        return Source('book', self.ID, **md)


class Catalog:
    def __init__(self, rows):
        self.items = [Record(**row) for row in rows]

    @classmethod
    def from_remote(cls):
        return cls(reader(
            io.StringIO(urllib.request.urlopen(URL).read().decode('utf8')),
            dicts=True, delimiter='\t'))

    @classmethod
    def from_local(cls, p):
        return cls(reader(p, dicts=True, delimiter='\t'))

    def write(self, dest):
        with UnicodeWriter(dest, delimiter='\t') as w:
            w.writerow([f.name for f in attr.fields(Record)])
            for item in self.items:
                w.writerow(attr.astuple(item))

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        for item in self.items:
            if item.has_open_license and item.year != 'Forthcoming':
                yield item

    def __getitem__(self, item):
        for it in self.items:
            if it.ID == item:
                return it
        else:
            raise KeyError(item)
